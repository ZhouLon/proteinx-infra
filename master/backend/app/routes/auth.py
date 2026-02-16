"""
认证路由
"""
import os
import json
import datetime
from fastapi import APIRouter, HTTPException, status, Form, Header, Body, Request
from app.config import USER_FILE, JWT_SECRET, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.models import LoginParams, RegisterParams
from app.utils.security import hash_password, create_access_token, create_refresh_token, jwt_decode

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.get("/exists")
def auth_exists():
    return {"exists": os.path.exists(USER_FILE)}

@router.post("/register")
def auth_register(params: RegisterParams):
    if os.path.exists(USER_FILE):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already registered")
    os.makedirs(os.path.dirname(USER_FILE), exist_ok=True)
    pwd_hash, salt_hex = hash_password(params.password)
    payload = {
        "username": params.username,
        "salt": salt_hex,
        "password_hash": pwd_hash,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    return {"ok": True}

@router.post("/token")
def auth_token(params: LoginParams, request: Request):
    from app.utils.security import ban_manager
    ip = request.client.host if request.client else ""
    if ip and ban_manager.is_banned(ip):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not os.path.exists(USER_FILE):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user registered")
    with open(USER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if params.username != data.get("username"):
        if ip:
            ban_manager.record_failure(ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    input_hash, _ = hash_password(params.password or "", data.get("salt"))
    if input_hash != data.get("password_hash"):
        if ip:
            ban_manager.record_failure(ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if ip:
        ban_manager.reset(ip)
    access = create_access_token(data.get("username"), ACCESS_TOKEN_EXPIRE_MINUTES, JWT_SECRET)
    refresh = create_refresh_token(data.get("username"), REFRESH_TOKEN_EXPIRE_DAYS, JWT_SECRET)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {"id": 1, "username": data.get("username"), "role": "admin"},
    }

@router.get("/me")
def auth_me(authorization: str = Header(None)):
    if not os.path.exists(USER_FILE):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user registered")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt_decode(token, JWT_SECRET)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    return {"id": 1, "username": payload.get("sub"), "role": "admin"}

@router.post("/refresh")
def auth_refresh(body: dict = Body(...)):
    rt = body.get("refresh_token")
    if not rt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing refresh_token")
    try:
        payload = jwt_decode(rt, JWT_SECRET)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    new_access = create_access_token(payload.get("sub"), ACCESS_TOKEN_EXPIRE_MINUTES, JWT_SECRET)
    return {"access_token": new_access, "token_type": "bearer"}
