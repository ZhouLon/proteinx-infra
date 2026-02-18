"""
配置管理模块：环境变量与路径
"""
import os
import logging

WORKDIR_CONTAINER = os.environ.get("WORKDIR_CONTAINER", "/data")
WORKDIR = WORKDIR_CONTAINER
USER_FILE = os.path.join(WORKDIR, ".user")
METADATA_DB = os.environ.get("METADATA_DB", os.path.join(WORKDIR, "metadata", "database.db"))
MUTATIONS_TABLE = "mutations"
SOURCES_TABLE = "sources"
MUTATION_REGEX = r"^([A-Za-z])(\d+)([A-Za-z])$"
METADATA_TABLE = os.environ.get("METADATA_TABLE", MUTATIONS_TABLE)
METADATA_DEFAULT_PAGE_SIZE = int(os.environ.get("METADATA_DEFAULT_PAGE_SIZE", "25"))
METADATA_MAX_PAGE_SIZE = int(os.environ.get("METADATA_MAX_PAGE_SIZE", "100"))
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "20"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
AUTH_FAIL_THRESHOLD = int(os.environ.get("AUTH_FAIL_THRESHOLD", "5"))
AUTH_FAIL_WINDOW_MINUTES = int(os.environ.get("AUTH_FAIL_WINDOW_MINUTES", "10"))
AUTH_BAN_MINUTES = int(os.environ.get("AUTH_BAN_MINUTES", "30"))
AUTH_BAN_LOG = os.path.join(WORKDIR, "logs", "auth_ban.log")
AUTH_BAN_STATE = os.path.join(WORKDIR, "security", "auth_ban_state.json")

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis-queue:6379/0")
JOB_QUEUE_NAME = os.environ.get("JOB_QUEUE_NAME", "job_queue")
INIT_QUEUE_NAME = os.environ.get("INIT_QUEUE_NAME", "init-queue")
STATE_QUEUE_NAME = os.environ.get("STATE_QUEUE_NAME", "state-queue")
RESULT_QUEUE_NAME = os.environ.get("RESULT_QUEUE_NAME", "results-queue")

os.makedirs(os.path.join(WORKDIR, "logs"), exist_ok=True)
os.makedirs(os.path.join(WORKDIR, "security"), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(WORKDIR, "logs", "backend.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)
