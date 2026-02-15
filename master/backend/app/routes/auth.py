"""
认证路由
"""
import os
import json
import datetime
from fastapi import APIRouter, HTTPException, status, Form
from app.config import USER_FILE
from app.models import LoginParams, RegisterParams
from app.utils.security import hash_password

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
def auth_token(params: LoginParams):
    if not os.path.exists(USER_FILE):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user registered")
    with open(USER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if params.username != data.get("username"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    input_hash, _ = hash_password(params.password or "", data.get("salt"))
    if input_hash != data.get("password_hash"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {
        "access_token": "mock_access",
        "refresh_token": "mock_refresh",
        "token_type": "bearer",
        "user": {"id": 1, "username": data.get("username"), "role": "admin"},
    }

@router.get("/me")
def auth_me():
    if not os.path.exists(USER_FILE):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user registered")
    with open(USER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"id": 1, "username": data.get("username"), "role": "admin"}

@router.post("/refresh")
def auth_refresh(refresh_token: str = Form(...)):
    return {"access_token": "mock_access_refreshed", "token_type": "bearer"}
