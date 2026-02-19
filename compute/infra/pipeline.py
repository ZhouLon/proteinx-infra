"""
数据管线：
- 读取 flags，保存配置快照
- 从 SQLite 检索数据集，落盘 selected.csv|parquet
- 执行嵌入与分集，写入 embeddings 与 splits
- 写入 metrics.jsonl 与 experiment.json 摘要
"""
from typing import Any, Dict, List
from pathlib import Path
import time
import json
import torch
import pandas as pd
from infra.flags import get_experiment_id
from infra.artifacts import ExperimentPaths
from infra.db.db import select_dataset
from infra.data.embedding.embedding import emb

def write_jsonl(path: Path, rows: List[Dict[str, Any]]):
    """追加写入 JSON Lines 文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def run(flags: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行完整数据管线并返回关键信息
    """
    exp_id = get_experiment_id(flags)
    paths = ExperimentPaths(exp_id)
    paths.prepare()
    data_query = {"conditions": flags.get("data.query", [])}
    pipeline_cfg = {
        "process": flags.get("data.process", {}),
        "embeddings": flags.get("embeddings", {}),
        "split": flags.get("split", {}),
    }
    paths.write_snapshot(flags, data_query, pipeline_cfg)
    df = select_dataset(flags)
    selected_path = paths.data / ("selected.parquet" if flags.get("data.format") == "parquet" else "selected.csv")
    if selected_path.suffix == ".parquet":
        df.to_parquet(selected_path, index=False)
    else:
        df.to_csv(selected_path, index=False)
    seq_field = flags.get("data.seq_field")
    emb_cfg = flags.get("embeddings", {})
    emb_type = emb_cfg.get("type")
    if emb_type and seq_field and seq_field in df.columns:
        seqs = df[seq_field].astype(str).tolist()
        x = emb(seqs, emb_type)
        torch.save(x, paths.embeddings / "data.pt")
    split_cfg = flags.get("split", {})
    if split_cfg.get("method") == "ratio":
        n = len(df)
        tr = max(0.0, min(1.0, float(split_cfg.get("train_ratio", 0.8))))
        vr = max(0.0, min(1.0, float(split_cfg.get("val_ratio", 0.1))))
        ti = int(n * tr)
        vi = int(n * vr)
        ids = list(range(n))
        train_ids = ids[:ti]
        val_ids = ids[ti:ti+vi]
        test_ids = ids[ti+vi:]
        Path(paths.splits / "train_ids.json").write_text(json.dumps(train_ids), encoding="utf-8")
        Path(paths.splits / "val_ids.json").write_text(json.dumps(val_ids), encoding="utf-8")
        Path(paths.splits / "test_ids.json").write_text(json.dumps(test_ids), encoding="utf-8")
    meta = {
        "experiment_id": exp_id,
        "created_at": int(time.time()),
        "status": "prepared",
        "records": len(df),
    }
    paths.write_experiment_meta(meta)
    write_jsonl(paths.metrics / "metrics.jsonl", [{"event": "prepared", "ts": int(time.time()), "records": len(df)}])
    return {"experiment_id": exp_id, "selected_path": str(selected_path)}
