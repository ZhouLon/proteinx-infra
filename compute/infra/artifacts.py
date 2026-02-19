"""
实验目录与产物管理：
- 负责创建标准化的实验目录结构，并写入快照与元信息
"""
from pathlib import Path
import json
from typing import Any, Dict
from infra.config import workdir
from infra.flags import save_json

class ExperimentPaths:
    """封装 experiment_id 下的所有子路径"""
    def __init__(self, experiment_id: str):
        base = workdir() / "experiments" / experiment_id
        self.root = base
        self.config = base / "config"
        self.data = base / "data"
        self.data_transform = self.data / "transform"
        self.embeddings = base / "embeddings"
        self.splits = base / "splits"
        self.logs = base / "logs"
        self.metrics = base / "metrics"
        self.ckpts = base / "ckpts"
        self.artifacts = base / "artifacts"
        self.experiment_json = base / "experiment.json"

    def prepare(self):
        """确保所有子目录存在"""
        for d in [
            self.root,
            self.config,
            self.data,
            self.data_transform,
            self.embeddings,
            self.splits,
            self.logs,
            self.metrics,
            self.ckpts,
            self.artifacts,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def write_snapshot(self, flags: Dict[str, Any], data_query: Dict[str, Any], pipeline_cfg: Dict[str, Any]):
        """写入 flags、数据查询与 pipeline 配置快照"""
        save_json(self.config / "flags.json", flags)
        save_json(self.config / "data_query.json", data_query)
        save_json(self.config / "pipeline.json", pipeline_cfg)

    def write_experiment_meta(self, meta: Dict[str, Any]):
        """写入实验元信息（experiment.json）"""
        save_json(self.experiment_json, meta)
