"""
flags 工具：
- 从文件读取/写入 JSON
- 从 flags 提取 experiment_id
"""
import json
from typing import Any, Dict
from pathlib import Path

def load_flags_from_path(p: Path) -> Dict[str, Any]:
    """从给定路径读取 JSON flags"""
    return json.loads(Path(p).read_text(encoding="utf-8"))

def save_json(p: Path, obj: Any):
    """将对象保存为 JSON 文件（确保父目录存在）"""
    p.parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def get_experiment_id(flags: Dict[str, Any]) -> str:
    """获取实验编号；若未设置则返回默认 'exp'"""
    v = flags.get("experiment_id")
    return str(v) if v is not None else "exp"
