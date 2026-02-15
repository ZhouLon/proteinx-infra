"""
数据模型定义（Pydantic）
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class LoginParams(BaseModel):
    username: str
    password: Optional[str] = None
    token: Optional[str] = None

class RegisterParams(BaseModel):
    username: str
    password: str

class NodeInfo(BaseModel):
    id: str
    ip: str
    hostname: str
    status: str
    resources: dict
    last_heartbeat: str

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

class DeleteParams(BaseModel):
    table: str
    ids: List[int]

class ProjectInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    created_at: str
    updated_at: str
    models_count: int = 0
    pinned_at: Optional[str] = None

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectDeleteParams(BaseModel):
    password: str

class DatasetCreate(BaseModel):
    name: str
    filters: List[Dict[str, Any]] = []
    table: Optional[str] = None

class DatasetInfo(BaseModel):
    id: str
    name: str
    filters: List[Dict[str, Any]]
    table: Optional[str]
    created_at: str
    rows_count: int

class RecycleItem(BaseModel):
    id: str
    name: str
    deleted_at: str
    original_path: str
