import os
import json
import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Body
from app.utils.projects import projects_root, read_project_info
from app.utils.queue import job_queue, push_init

router = APIRouter(prefix="/api/projects", tags=["jobs"])

def _jobs_dir(pid: str) -> str:
    """
    返回指定项目的 jobs 目录路径，若项目不存在则抛出 404。同时会创建 jobs 目录（若不存在）。
    - pid: 项目标识
    - 返回值: 形如 data/projects/<pid>/jobs 的绝对路径
    """
    root = projects_root()
    pdir = os.path.join(root, pid)
    if not os.path.isdir(pdir):
        raise HTTPException(status_code=404, detail="Project not found")
    jdir = os.path.join(pdir, "jobs")
    os.makedirs(jdir, exist_ok=True)
    return jdir

def _job_paths(pid: str, jid: str) -> Dict[str, str]:
    """
    构造某个任务在文件系统中的相关路径集合。
    - meta: 任务元信息JSON路径
    - log: 任务日志文件路径
    - state: 任务状态扩展JSON路径
    - cancel: 任务取消标记文件路径
    """
    jdir = _jobs_dir(pid)
    meta = os.path.join(jdir, f"{jid}.json")
    log = os.path.join(jdir, f"{jid}.log")
    state = os.path.join(jdir, f"{jid}.state.json")
    cancel = os.path.join(jdir, f"{jid}.cancel")
    return {"meta": meta, "log": log, "state": state, "cancel": cancel}

@router.post("/{pid}/jobs")
def create_job(pid: str, body: Dict[str, Any] = Body(...)):
    """
    创建并提交一个训练任务。
    - pid: 项目标识
    - body: 请求体，包含可选字段：
        - name: 任务名称，若为空则自动生成
        - config: 训练配置字典，默认为空字典
    - 返回: 包含新任务 id 的字典
    - 异常: 500 若 Redis 入队失败
    """

    read_project_info(pid)
    name = str(body.get("name") or f"experiment-{pid}")
    config = body.get("config") or {}
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    jid = f"job_id{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"
    paths = _job_paths(pid, jid)
    payload = {
        "pid": pid,
        "jid": jid,
        "name": name,
        "config": config,
        "created_at": now,
        "state": 0,
        "progress": 0,
        "used_time": 0,
    }
    try:
        job_queue.enqueue("worker_app.process_training", payload, job_id=jid)
        push_init(payload)
        return {"id": jid}
    except Exception as e:
        raise HTTPException(status_code=500, detail="队列入队失败，请检查Redis连接与认证配置")

@router.get("/{pid}/jobs")
def list_jobs(pid: str, status: Optional[str] = None, sort: Optional[str] = "time_desc"):
    jdir = _jobs_dir(pid)
    info_path = os.path.join(jdir, "jobs_info.json")
    items: List[Dict[str, Any]] = []
    if os.path.exists(info_path):
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    items = data
        except:
            items = []
    if status:
        mapping = {"PENDING": 0, "RUNNING": 1, "COMPLETED": 2, "FAILED": 3, "CANCELLED": 4}
        code = mapping.get(status.upper())
        if code is not None:
            items = [i for i in items if int(i.get("state", 0)) == code]
    keyfunc = lambda i: i.get("created_at", "")
    reverse = True
    if sort == "time_asc":
        reverse = False
    items.sort(key=keyfunc, reverse=reverse)
    return {"items": items, "total": len(items)}

@router.get("/{pid}/jobs/{jid}")
def job_detail(pid: str, jid: str):
    jdir = _jobs_dir(pid)
    info_path = os.path.join(jdir, "jobs_info.json")
    if not os.path.exists(info_path):
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        with open(info_path, "r", encoding="utf-8") as f:
            items = json.load(f)
        if not isinstance(items, list):
            raise HTTPException(status_code=404, detail="Job not found")
        base = next((i for i in items if str(i.get("jid") or i.get("id")) == jid), None)
        if not base:
            raise HTTPException(status_code=404, detail="Job not found")
    except:
        raise HTTPException(status_code=404, detail="Job not found")
    jsub = os.path.join(jdir, jid)
    state_path = os.path.join(jsub, "state.json")
    result_path = os.path.join(jsub, "result.json")
    detail = dict(base)
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                arr = json.load(f)
            if isinstance(arr, list) and arr:
                detail["last_state"] = arr[-1]
        except:
            pass
    if os.path.exists(result_path):
        try:
            with open(result_path, "r", encoding="utf-8") as f:
                arr = json.load(f)
            if isinstance(arr, list) and arr:
                detail["last_result"] = arr[-1]
        except:
            pass
    return detail
