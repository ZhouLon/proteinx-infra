"""
文件、作业与概览路由
"""
import os
import shutil
import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from app.config import WORKDIR
from app.models import FileInfo, Job, JobConfig, CreateJobParams, NodeInfo, Overview
from app.utils.path import get_real_path

router = APIRouter(tags=["files", "jobs", "overview"])

@router.get("/api/nodes", response_model=List[NodeInfo])
def list_nodes():
    now = datetime.datetime.utcnow().isoformat()
    return [
        NodeInfo(
            id="node-1",
            ip="192.168.1.101",
            hostname="worker-1",
            status="idle",
            resources={"cpu_usage": 10, "memory_usage": 20, "gpu_info": "RTX 3090"},
            last_heartbeat=now,
        )
    ]

@router.get("/api/nodes/{node_id}", response_model=NodeInfo)
def node_detail(node_id: str):
    now = datetime.datetime.utcnow().isoformat()
    return NodeInfo(
        id=node_id,
        ip="192.168.1.101",
        hostname="worker-1",
        status="idle",
        resources={"cpu_usage": 10, "memory_usage": 20, "gpu_info": "RTX 3090"},
        last_heartbeat=now,
    )

@router.post("/api/jobs", response_model=Job)
def create_job(params: CreateJobParams):
    now = datetime.datetime.utcnow().isoformat()
    return Job(
        id="job-1",
        name=params.name,
        status="pending",
        created_at=now,
        config=params.config,
    )

@router.get("/api/jobs", response_model=List[Job])
def list_jobs():
    now = datetime.datetime.utcnow().isoformat()
    return [
        Job(
            id="job-1",
            name="demo",
            status="running",
            created_at=now,
            started_at=now,
            config=JobConfig(
                model_type="pytorch",
                epochs=10,
                batch_size=32,
                learning_rate=0.001,
                dataset_path="/data/demo",
            ),
            node_id="node-1",
        )
    ]

@router.get("/api/jobs/{job_id}", response_model=Job)
def job_detail(job_id: str):
    now = datetime.datetime.utcnow().isoformat()
    return Job(
        id=job_id,
        name="demo",
        status="running",
        created_at=now,
        started_at=now,
        config=JobConfig(
            model_type="pytorch",
            epochs=10,
            batch_size=32,
            learning_rate=0.001,
            dataset_path="/data/demo",
        ),
        node_id="node-1",
    )

@router.get("/api/jobs/{job_id}/logs")
def job_logs(job_id: str):
    return "Mock log lines..."

@router.post("/api/jobs/{job_id}/cancel")
def job_cancel(job_id: str):
    return {"ok": True, "job_id": job_id, "status": "cancelled"}

@router.get("/api/files/list", response_model=List[FileInfo])
def files_list(path: str = "/"):
    real_path = get_real_path(path)
    if not os.path.exists(real_path):
        if path == "/" or path == "":
            os.makedirs(real_path, exist_ok=True)
        else:
            raise HTTPException(status_code=404, detail="Path not found")
    files = []
    try:
        with os.scandir(real_path) as it:
            for entry in it:
                if entry.name.startswith("."):
                    continue
                stats = entry.stat()
                files.append(FileInfo(
                    name=entry.name,
                    path=os.path.join(path, entry.name).replace("\\", "/"),
                    size=stats.st_size,
                    updated_at=datetime.datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    type="directory" if entry.is_dir() else "file"
                ))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return files

@router.post("/api/files/upload")
def files_upload(file: UploadFile = File(...), path: str = Form("/")):
    real_dir = get_real_path(path)
    if not os.path.exists(real_dir):
        os.makedirs(real_dir, exist_ok=True)
    file_path = os.path.join(real_dir, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"ok": True, "filename": file.filename, "path": path}

@router.delete("/api/files")
def files_delete(path: str):
    real_path = get_real_path(path)
    if not os.path.exists(real_path):
        raise HTTPException(status_code=404, detail="Path not found")
    try:
        if os.path.isdir(real_path):
            shutil.rmtree(real_path)
        else:
            os.remove(real_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"ok": True, "path": path}

@router.get("/api/files/preview")
def files_preview(path: str):
    real_path = get_real_path(path)
    if not os.path.exists(real_path) or not os.path.isfile(real_path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        with open(real_path, "r", encoding="utf-8") as f:
            content = f.read(4096)
        return content
    except Exception as e:
        return f"Cannot preview file: {str(e)}"

@router.get("/api/overview", response_model=Overview)
def overview():
    nodes = list_nodes()
    jobs = list_jobs()
    files_size_total = 0
    files_count = 0
    for root, dirs, files in os.walk(WORKDIR):
        for f in files:
            if f.startswith("."): 
                continue
            fp = os.path.join(root, f)
            try:
                files_size_total += os.path.getsize(fp)
                files_count += 1
            except:
                pass
    nodes_by_status = {}
    for node in nodes:
        nodes_by_status[node.status] = nodes_by_status.get(node.status, 0) + 1
    jobs_by_status = {}
    for job in jobs:
        jobs_by_status[job.status] = jobs_by_status.get(job.status, 0) + 1
    top_files = []
    try:
        top_files = files_list("/")
    except:
        pass
    return Overview(
        nodes_total=len(nodes),
        nodes_by_status=nodes_by_status,
        jobs_total=len(jobs),
        jobs_by_status=jobs_by_status,
        files_total=files_count,
        files_size_total=files_size_total,
        nodes=nodes,
        jobs=jobs,
        files=top_files,
    )
