"""
配置管理模块：环境变量与路径
"""
import os
import logging

WORKDIR_CONTAINER = os.environ.get("WORKDIR_CONTAINER", "/data")
WORKDIR = WORKDIR_CONTAINER
USER_FILE = os.path.join(WORKDIR, ".user")
METADATA_DB = os.path.join(WORKDIR, "metadata", "database.db")
METADATA_TABLE = os.environ.get("METADATA_TABLE", None)
METADATA_DEFAULT_PAGE_SIZE = int(os.environ.get("METADATA_DEFAULT_PAGE_SIZE", "25"))
METADATA_MAX_PAGE_SIZE = int(os.environ.get("METADATA_MAX_PAGE_SIZE", "100"))

os.makedirs(os.path.join(WORKDIR, "logs"), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(WORKDIR, "logs", "backend.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)
