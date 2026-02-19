"""
简易 Tensor 数据集封装，用于 Lightning 训练阶段
"""
from torch.utils.data import Dataset
import torch
from torch import Tensor
from typing import Optional

class MyDataset(Dataset):
    """封装特征与可选标签"""
    def __init__(self, features: Tensor, labels: Optional[Tensor] = None):
        self.features = features
        self.labels = labels

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        if self.labels is not None:
            return self.features[idx], self.labels[idx]
        return self.features[idx], torch.tensor(-1)
