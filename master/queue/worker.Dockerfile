FROM python:3.11-alpine
WORKDIR /app
RUN pip install --no-cache-dir rq redis
COPY worker_app.py /app/worker_app.py
COPY run_worker.py /app/run_worker.py
ENV PYTHONUNBUFFERED=1
CMD ["python", "/app/run_worker.py"]
