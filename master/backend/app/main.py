
"""
入口提示：
- 若需了解路由功能与各模块职责，请阅读 backend/INFO.md
牢记：如果对路由函数修改后，也需要更新 INFO.md 中的路由说明
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.routes.auth import router as auth_router
from app.routes.projects import router as projects_router
from app.routes.metadata import router as metadata_router
from app.routes.recycle import router as recycle_router
from app.routes.files_jobs_overview import router as fj_router
from app.config import WORKDIR
from app.utils.security import ban_manager
import os

app = FastAPI(title="ProteinX Infra Master API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IPBanMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else ""
        if ip and ban_manager.is_banned(ip):
            return Response(status_code=404)
        return await call_next(request)

app.add_middleware(IPBanMiddleware)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(metadata_router)
app.include_router(recycle_router)
app.include_router(fj_router)

os.makedirs(os.path.join(WORKDIR, "logs"), exist_ok=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
