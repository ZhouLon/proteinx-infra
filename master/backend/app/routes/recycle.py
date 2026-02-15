"""
回收站路由
"""
from fastapi import APIRouter
from app.services.project_service import (
    list_recycle_projects,
    restore_project_from_recycle,
    purge_recycle_item
)

router = APIRouter(prefix="/api/recycle", tags=["recycle"])

@router.get("/projects")
def recycle_list():
    return list_recycle_projects()

@router.post("/projects/{pid}/restore")
def recycle_restore(pid: str):
    return restore_project_from_recycle(pid)

@router.delete("/projects/{pid}")
def recycle_delete(pid: str):
    return purge_recycle_item(pid)
