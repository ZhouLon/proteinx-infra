"""
路径工具：工作目录安全映射
"""
import os
from fastapi import HTTPException
from app.config import WORKDIR

def get_real_path(path: str) -> str:
    clean_path = path.strip().lstrip("/")
    real_path = os.path.join(WORKDIR, clean_path)
    if not os.path.abspath(real_path).startswith(os.path.abspath(WORKDIR)):
        raise HTTPException(status_code=400, detail="Invalid path")
    return real_path
