import os
import json
import time
from typing import Dict, Any

WORKDIR = os.environ.get("WORKDIR_CONTAINER", "/data")

def _job_paths(pid: str, jid: str) -> Dict[str, str]:
    jdir = os.path.join(WORKDIR, "projects", pid, "jobs")
    os.makedirs(jdir, exist_ok=True)
    return {
        "meta": os.path.join(jdir, f"{jid}.json"),
        "log": os.path.join(jdir, f"{jid}.log"),
        "state": os.path.join(jdir, f"{jid}.state.json"),
        "cancel": os.path.join(jdir, f"{jid}.cancel"),
        "artifacts_dir": os.path.join(jdir, jid, "artifacts")
    }

def _write_log(path: str, line: str):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {line}\n")

def _read_cancel(cancel_path: str) -> bool:
    return os.path.exists(cancel_path)

def process_training(payload: Dict[str, Any]):
    pid = str(payload.get("pid"))
    jid = str(payload.get("jid"))
    cfg = payload.get("config") or {}
    paths = _job_paths(pid, jid)
    start_ts = time.time()
    # mark running
    try:
        with open(paths["meta"], "r", encoding="utf-8") as f:
            meta = json.load(f)
    except:
        meta = {"id": jid, "project_id": pid, "name": "experiment", "config": cfg}
    meta["status"] = "RUNNING"
    meta["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(paths["meta"], "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    _write_log(paths["log"], "job started")
    # simulate training progress
    for i in range(1, 11):
        if _read_cancel(paths["cancel"]):
            _write_log(paths["log"], "job cancelled by user")
            meta["status"] = "FAILED"
            meta["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            with open(paths["meta"], "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            return
        progress = i * 10
        state = {"progress": progress, "elapsed_ms": int((time.time() - start_ts) * 1000)}
        with open(paths["state"], "w", encoding="utf-8") as f:
            json.dump(state, f)
        _write_log(paths["log"], f"progress {progress}%")
        time.sleep(2)
    # simulate result artifact
    os.makedirs(paths["artifacts_dir"], exist_ok=True)
    artifact_path = os.path.join(paths["artifacts_dir"], "result.txt")
    with open(artifact_path, "w", encoding="utf-8") as f:
        f.write("training complete")
    _write_log(paths["log"], f"artifact written: {artifact_path}")
    meta["status"] = "SUCCEEDED"
    meta["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(paths["meta"], "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    _write_log(paths["log"], "job finished")
