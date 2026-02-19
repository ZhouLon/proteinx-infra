"""
Compute 平台的基础配置：
- 工作目录（由环境变量 PX_WORKDIR 指定）用于存放脚本、配置与所有实验产物
- 元数据库路径位于工作目录下的 /metadata/database.db
"""
import os
from pathlib import Path

def workdir() -> Path:
    """
    返回工作目录路径（PX_WORKDIR），并确保目录存在
    """
    p = Path(os.environ.get("PX_WORKDIR"))
    p.mkdir(parents=True, exist_ok=True)
    return p

def metadata_db_path() -> Path:
    """
    返回本地元数据库（SQLite）的文件路径，并确保父目录存在
    """
    base = workdir()
    db_dir = base / "metadata"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "database.db"
