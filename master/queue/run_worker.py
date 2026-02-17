import os
from rq import Worker, Queue, Connection
from redis import Redis

def main():
    url = os.environ.get("REDIS_URL", "redis://redis-queue:6379/0")
    qname = os.environ.get("TRAINING_QUEUE_NAME", "training-queue")
    conn = Redis.from_url(url)
    with Connection(conn):
        worker = Worker([Queue(qname, connection=conn)])
        worker.work()

if __name__ == "__main__":
    main()
