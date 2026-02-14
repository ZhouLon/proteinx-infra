from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import datetime
import os
import json
import shutil
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

# Configuration
WORKDIR = os.environ.get("WORKDIR_CONTAINER", "/data")
USER_FILE = os.path.join(WORKDIR, ".user")

class LoginParams(BaseModel):
    username: str
    password: Optional[str] = None
    token: Optional[str] = None

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
    os.makedirs(WORKDIR, exist_ok=True)
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

def get_real_path(path: str) -> str:
    # Ensure path starts with / and remove it to join correctly
    clean_path = path.strip().lstrip("/")
    real_path = os.path.join(WORKDIR, clean_path)
    # Security check to prevent path traversal
    if not os.path.abspath(real_path).startswith(os.path.abspath(WORKDIR)):
        raise HTTPException(status_code=400, detail="Invalid path")
    return real_path

@app.get("/api/files/list", response_model=List[FileInfo])
def files_list(path: str = "/"):
    real_path = get_real_path(path)
    if not os.path.exists(real_path):
         # If root, create it
        if path == "/" or path == "":
            os.makedirs(real_path, exist_ok=True)
        else:
            raise HTTPException(status_code=404, detail="Path not found")
            
    files = []
    try:
        with os.scandir(real_path) as it:
            for entry in it:
                if entry.name.startswith("."): # Skip hidden files
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

@app.post("/api/files/upload")
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

@app.delete("/api/files")
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

@app.get("/api/files/preview")
def files_preview(path: str):
    real_path = get_real_path(path)
    if not os.path.exists(real_path) or not os.path.isfile(real_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(real_path, "r", encoding="utf-8") as f:
            content = f.read(4096) # Read first 4KB
        return content
    except Exception as e:
        return f"Cannot preview file: {str(e)}"

@app.get("/api/overview", response_model=Overview)
def overview():
    nodes = list_nodes()
    jobs = list_jobs()
    
    # Calculate total file size recursively
    files_size_total = 0
    files_count = 0
    for root, dirs, files in os.walk(WORKDIR):
        for f in files:
            if f.startswith("."): continue
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
        
    # Get top level files for display list (mock for now in overview, or could call list)
    top_files = []
    try:
        # Re-use files_list logic for root
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
