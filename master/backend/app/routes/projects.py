"""
项目与数据集路由
"""
import datetime
import os
from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from app.models import ProjectInfo, ProjectCreate, ProjectUpdate, ProjectDeleteParams, DatasetCreate, DatasetInfo
from app.services.project_service import (
    projects_root, read_project_info, write_project_info,
    project_datasets_dir, create_dataset, list_datasets,
    delete_project_to_recycle
)
from app.utils.common import normalize_name

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("", response_model=List[ProjectInfo])
def list_projects():
    root = projects_root()
    items: List[ProjectInfo] = []
    with os.scandir(root) as it:
        for entry in it:
            if not entry.is_dir():
                continue
            try:
                items.append(read_project_info(entry.name))
            except:
                continue
    pinned = [i for i in items if i.pinned_at]
    unpinned = [i for i in items if not i.pinned_at]
    pinned.sort(key=lambda i: i.pinned_at or "", reverse=True)
    unpinned.sort(key=lambda i: i.created_at, reverse=True)
    items = pinned + unpinned
    return items

@router.post("", response_model=ProjectInfo)
def create_project(params: ProjectCreate):
    now = datetime.datetime.utcnow().isoformat()
    base = params.name.strip().lower().replace(" ", "-")
    pid = f"{base}-{int(datetime.datetime.utcnow().timestamp())}"
    norm_new = normalize_name(params.name)
    root = projects_root()
    with os.scandir(root) as it:
        for entry in it:
            if not entry.is_dir():
                continue
            try:
                info = read_project_info(entry.name)
                if normalize_name(info.name) == norm_new:
                    raise HTTPException(status_code=400, detail="项目名重复，请更换名字")
            except:
                continue
    info = ProjectInfo(
        id=pid,
        name=params.name.strip(),
        description=(params.description or "").strip(),
        created_at=now,
        updated_at=now,
        models_count=0,
        pinned_at=None,
    )
    write_project_info(info)
    return info

@router.get("/{pid}", response_model=ProjectInfo)
def project_detail(pid: str):
    return read_project_info(pid)

@router.patch("/{pid}", response_model=ProjectInfo)
def project_update(pid: str, params: ProjectUpdate):
    info = read_project_info(pid)
    changed = False
    if params.name is not None:
        info.name = params.name.strip()
        changed = True
    if params.description is not None:
        info.description = params.description.strip()
        changed = True
    if changed:
        info.updated_at = datetime.datetime.utcnow().isoformat()
        write_project_info(info)
    return info

@router.post("/{pid}/pin", response_model=ProjectInfo)
def project_pin(pid: str):
    info = read_project_info(pid)
    info.pinned_at = datetime.datetime.utcnow().isoformat()
    info.updated_at = datetime.datetime.utcnow().isoformat()
    write_project_info(info)
    return info

@router.post("/{pid}/unpin", response_model=ProjectInfo)
def project_unpin(pid: str):
    info = read_project_info(pid)
    info.pinned_at = None
    info.updated_at = datetime.datetime.utcnow().isoformat()
    write_project_info(info)
    return info

@router.delete("/{pid}")
def project_delete(pid: str, params: ProjectDeleteParams):
    return delete_project_to_recycle(pid, params.password)

@router.post("/{pid}/datasets", response_model=DatasetInfo)
def dataset_create(pid: str, params: DatasetCreate):
    return create_dataset(pid, params.name, params.filters, params.table)

@router.get("/{pid}/datasets")
def dataset_list(pid: str, page: int = 1, per_page: int = 10):
    return list_datasets(pid, page, per_page)
