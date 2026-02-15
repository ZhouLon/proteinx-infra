"""
项目与数据集业务逻辑
"""
import os
import json
import shutil
import datetime
from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from app.config import WORKDIR, USER_FILE
from app.models import ProjectInfo, DatasetInfo
from app.utils.security import hash_password
from app.utils.common import normalize_name
from app.utils.db import get_db_conn, resolve_table, build_where_clause

def projects_root() -> str:
    root = os.path.join(WORKDIR, "projects")
    os.makedirs(root, exist_ok=True)
    return root

def read_project_info(pid: str) -> ProjectInfo:
    root = projects_root()
    pdir = os.path.join(root, pid)
    info_path = os.path.join(pdir, "info.json")
    if not os.path.exists(info_path):
        raise HTTPException(status_code=404, detail="Project not found")
    with open(info_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ProjectInfo(**data)

def write_project_info(info: ProjectInfo):
    root = projects_root()
    pdir = os.path.join(root, info.id)
    os.makedirs(pdir, exist_ok=True)
    info_path = os.path.join(pdir, "info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info.dict(), f, ensure_ascii=False, indent=2)

def project_datasets_dir(pid: str) -> str:
    root = projects_root()
    pdir = os.path.join(root, pid)
    if not os.path.isdir(pdir):
        raise HTTPException(status_code=404, detail="Project not found")
    ddir = os.path.join(pdir, "datasets")
    os.makedirs(ddir, exist_ok=True)
    return ddir

def create_dataset(pid: str, name: str, filters: List[Dict[str, Any]], table: Optional[str]) -> DatasetInfo:
    ddir = project_datasets_dir(pid)
    conn = get_db_conn()
    try:
        real_table = resolve_table(conn, table)
        cur = conn.execute(f"PRAGMA table_info({real_table})")
        valid_cols = {row["name"] for row in cur.fetchall()}
        where_sql, where_params = build_where_clause(filters, valid_cols)
        count_sql = f"SELECT COUNT(*) as cnt FROM {real_table} {where_sql}"
        cur = conn.execute(count_sql, where_params)
        rows_count = cur.fetchone()["cnt"]
    finally:
        conn.close()
    now = datetime.datetime.utcnow().isoformat()
    did = f"ds-{int(datetime.datetime.utcnow().timestamp())}"
    info = DatasetInfo(
        id=did,
        name=name.strip(),
        filters=filters or [],
        table=table,
        created_at=now,
        rows_count=rows_count,
    )
    info_path = os.path.join(ddir, f"{did}.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info.dict(), f, ensure_ascii=False, indent=2)
    return info

def list_datasets(pid: str, page: int = 1, per_page: int = 10):
    ddir = project_datasets_dir(pid)
    items: List[DatasetInfo] = []
    with os.scandir(ddir) as it:
        for entry in it:
            if entry.is_file() and entry.name.endswith(".json"):
                try:
                    with open(os.path.join(ddir, entry.name), "r", encoding="utf-8") as f:
                        data = json.load(f)
                    items.append(DatasetInfo(**data))
                except:
                    continue
    items.sort(key=lambda x: x.created_at, reverse=True)
    total = len(items)
    if page < 1 or per_page < 1:
        raise HTTPException(status_code=400, detail="Invalid pagination")
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]
    return {"items": [i.dict() for i in page_items], "total": total, "page": page, "per_page": per_page}

def recycle_root() -> str:
    root = os.path.join(WORKDIR, "recycle_bin")
    os.makedirs(root, exist_ok=True)
    return root

def delete_project_to_recycle(pid: str, password: str):
    if not os.path.exists(USER_FILE):
        raise HTTPException(status_code=404, detail="No user registered")
    with open(USER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    input_hash, _ = hash_password(password or "", data.get("salt"))
    if input_hash != data.get("password_hash"):
        raise HTTPException(status_code=401, detail="Invalid password")
    root = projects_root()
    pdir = os.path.join(root, pid)
    if not os.path.isdir(pdir):
        raise HTTPException(status_code=404, detail="Project not found")
    info = read_project_info(pid)
    rroot = recycle_root()
    dest = os.path.join(rroot, pid)
    if os.path.exists(dest):
        raise HTTPException(status_code=409, detail="Recycle destination exists")
    shutil.move(pdir, dest)
    deleted_meta = {
        "id": pid,
        "name": info.name,
        "deleted_at": datetime.datetime.utcnow().isoformat(),
        "original_path": pdir
    }
    with open(os.path.join(dest, ".deleted.json"), "w", encoding="utf-8") as f:
        json.dump(deleted_meta, f, ensure_ascii=False, indent=2)
    return {"ok": True, "id": pid}

def list_recycle_projects():
    root = recycle_root()
    items: List[dict] = []
    now = datetime.datetime.utcnow()
    purge_before = now - datetime.timedelta(days=30)
    from app.models import RecycleItem
    with os.scandir(root) as it:
        for entry in it:
            if not entry.is_dir():
                continue
            pdir = os.path.join(root, entry.name)
            meta_path = os.path.join(pdir, ".deleted.json")
            try:
                if os.path.exists(meta_path):
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    deleted_at = datetime.datetime.fromisoformat(meta.get("deleted_at"))
                    if deleted_at < purge_before:
                        shutil.rmtree(pdir)
                        continue
                    items.append(RecycleItem(**meta).dict())
                else:
                    info_path = os.path.join(pdir, "info.json")
                    if os.path.exists(info_path):
                        with open(info_path, "r", encoding="utf-8") as f:
                            info = json.load(f)
                        deleted_at = datetime.datetime.utcfromtimestamp(os.path.getmtime(pdir)).isoformat()
                        items.append(RecycleItem(id=entry.name, name=info.get("name", entry.name), deleted_at=deleted_at, original_path="").dict())
            except:
                continue
    items.sort(key=lambda x: x["deleted_at"], reverse=True)
    return {"items": items}

def restore_project_from_recycle(pid: str):
    rroot = recycle_root()
    proot = projects_root()
    src = os.path.join(rroot, pid)
    if not os.path.isdir(src):
        raise HTTPException(status_code=404, detail="Not found in recycle")
    info_path = os.path.join(src, "info.json")
    if not os.path.exists(info_path):
        raise HTTPException(status_code=400, detail="Missing info.json")
    with open(info_path, "r", encoding="utf-8") as f:
        info_data = json.load(f)
    name_norm = normalize_name(info_data.get("name", ""))
    with os.scandir(proot) as it:
        for entry in it:
            if not entry.is_dir():
                continue
            try:
                info = read_project_info(entry.name)
            except:
                continue
            if normalize_name(info.name) == name_norm:
                raise HTTPException(status_code=409, detail="已有的项目名称冲突重复，无法还原")
    dest = os.path.join(proot, pid)
    if os.path.exists(dest):
        raise HTTPException(status_code=409, detail="目标已存在，无法还原")
    shutil.move(src, dest)
    return {"ok": True, "id": pid}

def purge_recycle_item(pid: str):
    rroot = recycle_root()
    src = os.path.join(rroot, pid)
    if not os.path.isdir(src):
        raise HTTPException(status_code=404, detail="Not found in recycle")
    shutil.rmtree(src)
    return {"ok": True, "id": pid}
