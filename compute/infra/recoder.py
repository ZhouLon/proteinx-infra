"""
实验目录与产物管理：
- 负责创建标准化的实验目录结构，并写入快照与元信息
"""
import json
from typing import Any, Dict
import datetime
from pathlib import Path

class ExperimentRecorder:
    
    
    def create_dirs(self, workdir: str, experiment_id: str):
        """封装 experiment_id 下的所有子路径"""
        self.base = Path(workdir) / "experiments" / experiment_id
        self.root = self.base
        self.result_flag = "Success"
        self.time_flag = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.exp_plan_config = self.base / "exp_plan.json"  #记录本次实验计划
        self.training = self.base / "training"  #记录实验训练过程,包括训练的和验证的loss，acc/mae，lr，时间
        self.pth = self.base / "model.pth"  #记录实验训练好的模型权重
        self.labels = self.base / "labels.npz"  #记录实验数据的标签
        self.metrics = self.base / "metrics.json"  #记录实验结果指标
        self.visualization = self.base / "visualization"  #记录实验可视化结果的图片

        # 确保所有子目录存在
        for d in [
            self.root,
            self.training,
            self.visualization,
        ]:d.mkdir(parents=True, exist_ok=True)


