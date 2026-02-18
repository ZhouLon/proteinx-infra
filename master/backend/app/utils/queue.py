import os
import json
from typing import Any, Optional, Tuple, List
from redis import Redis
from rq import Queue
from app.config import REDIS_URL, JOB_QUEUE_NAME, INIT_QUEUE_NAME, STATE_QUEUE_NAME, RESULT_QUEUE_NAME


_redis = Redis.from_url(REDIS_URL)
job_queue = Queue(JOB_QUEUE_NAME, connection=_redis)

def get_redis() -> Redis:
    return _redis

def _init_key() -> str:
    return os.environ.get("INIT_QUEUE_NAME", INIT_QUEUE_NAME)

def _state_key() -> str:
    return os.environ.get("STATE_QUEUE_NAME", STATE_QUEUE_NAME)

def _results_key() -> str:
    return os.environ.get("RESULTS_QUEUE_NAME", RESULT_QUEUE_NAME)

def push_init(obj: Any) -> int:
    return _redis.rpush(_init_key(), json.dumps(obj, ensure_ascii=False))

def push_state(obj: Any) -> int:
    return _redis.rpush(_state_key(), json.dumps(obj, ensure_ascii=False))

def push_result(obj: Any) -> int:
    return _redis.rpush(_results_key(), json.dumps(obj, ensure_ascii=False))

def brpop_init(timeout: int = 1) -> Optional[Tuple[str, str]]:
    return _redis.brpop(_init_key(), timeout=timeout)

def brpop_state(timeout: int = 1) -> Optional[Tuple[str, str]]:
    return _redis.brpop(_state_key(), timeout=timeout)

def brpop_result(timeout: int = 1) -> Optional[Tuple[str, str]]:
    return _redis.brpop(_results_key(), timeout=timeout)

def brpop_all(timeout: int = 1) -> Optional[Tuple[str, str]]:
    keys: List[str] = [_init_key(), _state_key(), _results_key()]
    return _redis.brpop(keys, timeout=timeout)
