"""
保存器（Saver）模块
-------------------
职责：
- 在后端服务生命周期中启动一个异步后台任务，每秒从 Redis 中的三个队列取数并落盘：
  - INIT_QUEUE_NAME：初始化任务信息流（每个新任务入队一次）
  - STATE_QUEUE_NAME：训练中的状态流（进度、指标等，可能多次入队）
  - RESULTS_QUEUE_NAME：训练完成后的结果流（一次或少量次数）

数据组织：
- 项目级目录：data/projects/<pid>/jobs/
  - jobs_info.json：数组，保存多个任务的初始化信息（来自 init-queue）
- 任务级目录：data/projects/<pid>/jobs/<jid>/
  - state.json：数组，按时间追加 state 载荷
  - result.json：数组，按时间追加 result 载荷

实现要点：
- 使用 Redis 异步客户端（redis.asyncio），通过 BRPOP(keys, timeout=1) 以 1 秒节奏阻塞获取队列数据
- 文件写入采用原子写（临时文件 + os.replace），防止部分写入导致 JSON 损坏
- 后台任务绑定在单进程的 FastAPI lifespan 内，优雅停机时设置停止事件并收尾
"""
import os
import json
import asyncio
from typing import Dict, Any, List
from redis.asyncio import Redis
from app.utils.projects import projects_root

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis-queue:6379/0")
INIT_QUEUE_NAME = os.environ.get("INIT_QUEUE_NAME", "init_queue")
STATE_QUEUE_NAME = os.environ.get("STATE_QUEUE_NAME", "state_queue")
RESULTS_QUEUE_NAME = os.environ.get("RESULTS_QUEUE_NAME", "results_queue")
SAVER_POLL_TIMEOUT = int(os.environ.get("SAVER_POLL_TIMEOUT", "1"))

def _jobs_dir(pid: str) -> str:
    """
    返回项目的 jobs 目录路径，若不存在则创建。
    - pid: 项目标识
    - 返回值: data/projects/<pid>/jobs 绝对路径
    """
    root = projects_root()
    pdir = os.path.join(root, pid)
    jdir = os.path.join(pdir, "jobs")
    os.makedirs(jdir, exist_ok=True)
    return jdir

def _write_json_atomic(path: str, obj: Any) -> None:
    """
    原子写 JSON：
    - 先写到同目录的临时文件 path.tmp
    - 再用 os.replace 覆盖目标文件，保证写入的原子性
    """
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def _job_dir(pid: str, jid: str) -> str:
    """
    返回任务级子目录路径 data/projects/<pid>/jobs/<jid>，若不存在则创建。
    """
    jdir = _jobs_dir(pid)
    jsub = os.path.join(jdir, jid)
    os.makedirs(jsub, exist_ok=True)
    return jsub

def _append_json_array(path: str, obj: Dict[str, Any]) -> None:
    """
    将对象追加到指定 JSON 数组文件：
    - 文件不存在则创建空数组
    - 文件存在则读取为数组并在末尾追加
    - 使用原子写回盘
    """
    arr: List[Dict[str, Any]] = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    arr = data
        except:
            arr = []
    arr.append(obj)
    _write_json_atomic(path, arr)


async def run_saver(stop: asyncio.Event) -> None:
    """
    后台保存器主循环：
    - 每次 BRPOP 同时监听 init/state/results 三个队列，timeout=1 保证每秒节奏
    - 根据队列类型进行不同的落盘策略：
      * init-queue：jobs_info.json 追加、创建任务子目录并预建空的 state.json/result.json
      * state-queue：将载荷追加到任务子目录的 state.json
      * results-queue：将载荷追加到任务子目录的 result.json
    - 停止条件：收到 stop 事件（由 FastAPI lifespan 在停机时触发）
    """
    redis = Redis.from_url(REDIS_URL, decode_responses=True)
    try:
        while not stop.is_set():
            item = await redis.brpop([INIT_QUEUE_NAME, STATE_QUEUE_NAME, RESULTS_QUEUE_NAME], timeout=SAVER_POLL_TIMEOUT)
            if not item:
                continue
            key, value = item
            try:
                payload = json.loads(value)
            except:
                continue
            pid = str(payload.get("pid"))
            jid = str(payload.get("jid"))
            if not pid or not jid:
                continue
            if key == INIT_QUEUE_NAME:
                jdir = _jobs_dir(pid)
                info_path = os.path.join(jdir, "jobs_info.json")
                _append_json_array(info_path, payload)
                jsub = _job_dir(pid, jid)
                state_path = os.path.join(jsub, "state.json")
                result_path = os.path.join(jsub, "result.json")
                if not os.path.exists(state_path):
                    _write_json_atomic(state_path, [])
                if not os.path.exists(result_path):
                    _write_json_atomic(result_path, [])
            elif key == STATE_QUEUE_NAME:
                jsub = _job_dir(pid, jid)
                state_path = os.path.join(jsub, "state.json")
                _append_json_array(state_path, payload)
            else:
                jsub = _job_dir(pid, jid)
                result_path = os.path.join(jsub, "result.json")
                _append_json_array(result_path, payload)
            # 让出事件循环，避免长时间占用
            await asyncio.sleep(0)
    finally:
        # 优雅关闭 Redis 连接
        await redis.close()
