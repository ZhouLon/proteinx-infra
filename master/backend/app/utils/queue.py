import os
from redis import Redis
from rq import Queue

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis-queue:6379/0")
TRAINING_QUEUE_NAME = os.environ.get("TRAINING_QUEUE_NAME", "training-queue")
RESULTS_QUEUE_NAME = os.environ.get("RESULTS_QUEUE_NAME", "results-queue")

_redis = Redis.from_url(REDIS_URL)
training_queue = Queue(TRAINING_QUEUE_NAME, connection=_redis)
results_queue = Queue(RESULTS_QUEUE_NAME, connection=_redis)

def get_redis():
    return _redis
