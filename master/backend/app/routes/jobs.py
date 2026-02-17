import os
import json
import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Body
from app.config import WORKDIR
from app.services.project_service import projects_root, read_project_info
from app.utils.queue import training_queue

router = APIRouter(prefix="/api/projects", tags=["jobs"])

def _jobs_dir(pid: str) -> str:
    root = projects_root()
    pdir = os.path.join(root, pid)
    if not os.path.isdir(pdir):
        raise HTTPException(status_code=404, detail="Project not found")
    jdir = os.path.join(pdir, "jobs")
    os.makedirs(jdir, exist_ok=True)
    return jdir

def _job_paths(pid: str, jid: str) -> Dict[str, str]:
    jdir = _jobs_dir(pid)
    meta = os.path.join(jdir, f"{jid}.json")
    log = os.path.join(jdir, f"{jid}.log")
    state = os.path.join(jdir, f"{jid}.state.json")
    cancel = os.path.join(jdir, f"{jid}.cancel")
    return {"meta": meta, "log": log, "state": state, "cancel": cancel}

@router.post("/{pid}/jobs")
def create_job(pid: str, body: Dict[str, Any] = Body(...)):
    read_project_info(pid)
    name = str(body.get("name") or f"experiment-{pid}")
    config = body.get("config") or {}
    now = datetime.datetime.utcnow().isoformat()
    jid = f"job-{int(datetime.datetime.utcnow().timestamp())}"
    paths = _job_paths(pid, jid)
    meta = {
        "id": jid,
        "project_id": pid,
        "name": name,
        "status": "PENDING",
        "created_at": now,
        "config": config,
        "progress": 0,
        "elapsed_ms": 0,
    }
    os.makedirs(os.path.dirname(paths["meta"]), exist_ok=True)
    with open(paths["meta"], "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    with open(paths["log"], "w", encoding="utf-8") as f:
        f.write(f"[{now}] job created\n")
    payload = {"pid": pid, "jid": jid, "config": config}
    try:
        training_queue.enqueue("worker_app.process_training", payload, job_id=jid)
        return {"id": jid}
    except Exception as e:
        with open(paths["log"], "a", encoding="utf-8") as f:
            f.write(f"[{now}] enqueue failed: {e}\n")
        meta["status"] = "FAILED"
        with open(paths["meta"], "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        raise HTTPException(status_code=500, detail="队列入队失败，请检查Redis连接与认证配置")

@router.get("/{pid}/jobs")
def list_jobs(pid: str, status: Optional[str] = None, sort: Optional[str] = "time_desc"):
    jdir = _jobs_dir(pid)
    items: List[Dict[str, Any]] = []
    with os.scandir(jdir) as it:
        for entry in it:
            if entry.is_file() and entry.name.endswith(".json"):
                try:
                    with open(os.path.join(jdir, entry.name), "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    items.append(meta)
                except:
                    continue
    if status:
        items = [i for i in items if str(i.get("status")).upper() == status.upper()]
    keyfunc = lambda i: i.get("created_at", "")
    reverse = True
    if sort == "time_asc":
        reverse = False
    items.sort(key=keyfunc, reverse=reverse)
    return {"items": items, "total": len(items)}

@router.get("/{pid}/jobs/{jid}")
def job_detail(pid: str, jid: str):
    paths = _job_paths(pid, jid)
    if not os.path.exists(paths["meta"]):
        raise HTTPException(status_code=404, detail="Job not found")
    with open(paths["meta"], "r", encoding="utf-8") as f:
        meta = json.load(f)
    if os.path.exists(paths["state"]):
        try:
            with open(paths["state"], "r", encoding="utf-8") as f:
                state = json.load(f)
            meta.update(state)
        except:
            pass
    return meta

@router.get("/{pid}/jobs/{jid}/logs")
def job_logs(pid: str, jid: str):
    paths = _job_paths(pid, jid)
    if not os.path.exists(paths["log"]):
        return {"logs": ""}
    with open(paths["log"], "r", encoding="utf-8") as f:
        content = f.read()
    return {"logs": content}

@router.post("/{pid}/jobs/{jid}/cancel")
def job_cancel(pid: str, jid: str):
    paths = _job_paths(pid, jid)
    with open(paths["cancel"], "w", encoding="utf-8") as f:
        f.write("1")
    return {"ok": True}
