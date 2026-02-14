from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import datetime
import os
import json
from fastapi import HTTPException, status
import hashlib
import binascii

app = FastAPI(title="ProteinX Infra Master API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginParams(BaseModel):
    username: str
    password: Optional[str] = None
    token: Optional[str] = None

 

 

USER_FILE = "/data/.user"

class RegisterParams(BaseModel):
    username: str
    password: str

def hash_password(password: str, salt_hex: Optional[str] = None) -> (str, str):
    if salt_hex is None:
        salt = os.urandom(16)
        salt_hex = binascii.hexlify(salt).decode("utf-8")
    else:
        salt = binascii.unhexlify(salt_hex.encode("utf-8"))
    h = hashlib.sha256(salt + password.encode("utf-8")).hexdigest()
    return h, salt_hex

@app.get("/api/auth/exists")
def auth_exists():
    return {"exists": os.path.exists(USER_FILE)}

@app.post("/api/auth/register")
def auth_register(params: RegisterParams):
    if os.path.exists(USER_FILE):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already registered")
    os.makedirs("/data", exist_ok=True)
    pwd_hash, salt_hex = hash_password(params.password)
    payload = {
        "username": params.username,
        "salt": salt_hex,
        "password_hash": pwd_hash,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    return {"ok": True}

@app.post("/api/auth/token")
def auth_token(params: LoginParams):
    if not os.path.exists(USER_FILE):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user registered")
    with open(USER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if params.username != data.get("username"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    input_hash, _ = hash_password(params.password or "", data.get("salt"))
    if input_hash != data.get("password_hash"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {
        "access_token": "mock_access",
        "refresh_token": "mock_refresh",
        "token_type": "bearer",
        "user": {"id": 1, "username": data.get("username"), "role": "admin"},
    }

@app.get("/api/auth/me")
def auth_me():
    if not os.path.exists(USER_FILE):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user registered")
    with open(USER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"id": 1, "username": data.get("username"), "role": "admin"}

@app.post("/api/auth/refresh")
def auth_refresh(refresh_token: str = Form(...)):
    return {"access_token": "mock_access_refreshed", "token_type": "bearer"}

class NodeInfo(BaseModel):
    id: str
    ip: str
    hostname: str
    status: str
    resources: dict
    last_heartbeat: str

@app.get("/api/nodes", response_model=List[NodeInfo])
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

@app.get("/api/nodes/{node_id}", response_model=NodeInfo)
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

class JobConfig(BaseModel):
    model_type: str
    epochs: int
    batch_size: int
    learning_rate: float
    dataset_path: str

class Job(BaseModel):
    id: str
    name: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    config: JobConfig
    node_id: Optional[str] = None

class FileInfo(BaseModel):
    name: str
    path: str
    size: int
    updated_at: str
    type: str

class Overview(BaseModel):
    nodes_total: int
    nodes_by_status: dict
    jobs_total: int
    jobs_by_status: dict
    files_total: int
    files_size_total: int
    nodes: List[NodeInfo]
    jobs: List[Job]
    files: List[FileInfo]

class CreateJobParams(BaseModel):
    name: str
    config: JobConfig

@app.post("/api/jobs", response_model=Job)
def create_job(params: CreateJobParams):
    now = datetime.datetime.utcnow().isoformat()
    return Job(
        id="job-1",
        name=params.name,
        status="pending",
        created_at=now,
        config=params.config,
    )

@app.get("/api/jobs", response_model=List[Job])
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

@app.get("/api/jobs/{job_id}", response_model=Job)
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

@app.get("/api/jobs/{job_id}/logs")
def job_logs(job_id: str):
    return "Mock log lines..."

@app.post("/api/jobs/{job_id}/cancel")
def job_cancel(job_id: str):
    return {"ok": True, "job_id": job_id, "status": "cancelled"}

@app.get("/api/files/list", response_model=List[FileInfo])
def files_list(path: str = "/"):
    return [
        FileInfo(
            name="demo.fasta",
            path=f"{path}/demo.fasta",
            size=1234,
            updated_at=datetime.datetime.utcnow().isoformat(),
            type="file",
        )
    ]

@app.post("/api/files/upload")
def files_upload(file: UploadFile = File(...), path: str = Form("/")):
    return {"ok": True, "filename": file.filename, "path": path}

@app.delete("/api/files")
def files_delete(path: str):
    return {"ok": True, "path": path}

@app.get("/api/files/preview")
def files_preview(path: str):
    return "Mock file preview: header and first lines"

@app.get("/api/overview", response_model=Overview)
def overview():
    nodes = list_nodes()
    jobs = list_jobs()
    files = files_list("/")
    nodes_by_status = {}
    for node in nodes:
        nodes_by_status[node.status] = nodes_by_status.get(node.status, 0) + 1
    jobs_by_status = {}
    for job in jobs:
        jobs_by_status[job.status] = jobs_by_status.get(job.status, 0) + 1
    files_size_total = sum(file.size for file in files if file.type == "file")
    return Overview(
        nodes_total=len(nodes),
        nodes_by_status=nodes_by_status,
        jobs_total=len(jobs),
        jobs_by_status=jobs_by_status,
        files_total=len(files),
        files_size_total=files_size_total,
        nodes=nodes,
        jobs=jobs,
        files=files,
    )
