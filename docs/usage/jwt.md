# JWT 使用与最佳实践

JWT（JSON Web Token）是一种无状态的认证令牌格式，常用于前后端分离场景的身份认证与授权。它通过数字签名保证令牌不可伪造，令牌本身携带必要的用户与会话信息（Claims），后端据此进行访问控制。

## 核心概念

- 令牌结构：`header.payload.signature`，三段均采用 Base64URL 编码
  - Header：算法与类型，如 `{ alg: "HS256", typ: "JWT" }`
  - Payload：声明（Claims），如 `sub`（用户ID）、`exp`（过期时间）等
  - Signature：使用密钥对前两段签名，防止篡改
- Access Token 与 Refresh Token
  - Access Token：短期令牌，用于访问受保护资源，通常 5–30 分钟过期
  - Refresh Token：长期令牌，仅用于刷新 Access Token，通常 7–30 天过期，需更严格保护与撤销策略

## 工作流程

- 登录
  - 用户提交用户名与密码
  - 后端校验成功后签发 Access Token 与 Refresh Token
- 访问受保护资源
  - 前端将 Access Token 通过请求头 `Authorization: Bearer <token>` 发送
  - 后端验证签名与过期时间，放行或拒绝
- 刷新令牌
  - Access Token 过期时，使用 Refresh Token 获取新的 Access Token（可轮换刷新令牌）
- 登出/撤销
  - 将 Refresh Token 加入黑名单或数据库标记为失效，强制重新认证

## 前端存储与传输

- 推荐
  - 将 Access Token 存储在内存或短期存储（如 sessionStorage）
  - Refresh Token 放在 HttpOnly Cookie（防XSS），配合 SameSite=Lax/Strict，且仅在刷新接口使用
  - 使用 `Authorization: Bearer <access_token>` 作为请求头访问受保护 API
- 注意
  - 避免将令牌长期保存在 localStorage（易受XSS影响）
  - 所有通信必须在 HTTPS 下进行，避免令牌被窃听
  - 跨站请求时考虑 CSRF 防护（Cookie 场景尤其重要）

## 后端实现示例（FastAPI + python-jose）

> 以下示例代码仅用于教学，实际项目需要完善密码存储、速率限制、黑名单/撤销、审计日志等安全措施。

```python
# 安装依赖
# pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt]

import os
import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

SECRET_KEY = os.environ.get("JWT_SECRET", "change-me-in-env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
app = FastAPI()

def create_token(data: dict, expires_delta: datetime.timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "iat": datetime.datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(user_id: str) -> str:
    return create_token({"sub": user_id, "type": "access"}, datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

def create_refresh_token(user_id: str) -> str:
    return create_token({"sub": user_id, "type": "refresh"}, datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

def verify_token(token: str, expected_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    payload = verify_token(token, "access")
    return payload.get("sub")

@app.post("/api/auth/token")
def login(username: str, password: str):
    # TODO: 校验用户名密码（哈希对比）
    if not username or not password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    access = create_access_token(user_id=username)
    refresh = create_refresh_token(user_id=username)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

@app.post("/api/auth/refresh")
def refresh_token(refresh_token: str):
    payload = verify_token(refresh_token, "refresh")
    user_id = payload.get("sub")
    # 可选：刷新令牌轮换与黑名单校验
    new_access = create_access_token(user_id)
    return {"access_token": new_access, "token_type": "bearer"}

@app.get("/api/secure/me")
def me(current_user: str = Depends(get_current_user)):
    return {"id": current_user, "role": "user"}
```

## 接入到当前项目的指引

- 后端
  - 在环境变量中设置 `JWT_SECRET`（外部 .env 或 Docker env_file）
  - 将登录接口 `/api/auth/token` 替换为真实签发 JWT 的实现（返回 access_token 与 refresh_token）
  - 在受保护路由添加依赖校验（读取 `Authorization: Bearer <access_token>` 并验证）
  - 实现 `/api/auth/refresh` 刷新令牌与轮换逻辑
  - 缩紧 CORS 配置，仅允许你的前端域名
- 前端
  - 登录后，将 access_token 写入内存（或 sessionStorage），请求时设置 `Authorization` 头
  - 统一封装 axios 拦截器：当收到 401 时使用 refresh_token 刷新 access_token 并重试；刷新失败则跳转登录
  - 可选：将 refresh_token 存在 HttpOnly Cookie，配合 SameSite 与 CSRF 防护

## 安全最佳实践清单

- 强随机密钥（SECRET_KEY）放在容器外部，通过环境变量注入
- Access Token 设置短过期，Refresh Token 设置长过期并支持轮换与撤销
- 所有接口仅在 HTTPS 下使用；限制 CORS
- 重要写操作接口增加速率限制与审计日志
- 对 Refresh Token 使用 HttpOnly Cookie 并做 CSRF 防护
- 在 Claims 中使用 `iss`（签发方）、`aud`（受众）等，增强校验
- 令牌泄露应支持即时撤销（黑名单）与全局密钥滚动

---

更多：你可以结合当前项目的路由与登录页面，将临时的 Cookie 门禁替换为 JWT 门禁（access_token 控制页面访问，refresh_token 管理续期）。在生产环境务必使用 HTTPS，并将所有敏感配置放在 Docker 外部的 env/secrets 管理中。 
