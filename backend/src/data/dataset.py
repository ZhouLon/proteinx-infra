from torch.utils.data import Dataset
import torch
from torch import Tensor
from typing import Tuple, Optional, Union, List, Dict

class MyDataset(Dataset):
    """自定义Tensor数据集类"""
    def __init__(self, features: Tensor, labels: Optional[Tensor] = None):
        self.features = features
        self.labels = labels
        
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        if self.labels is not None:
            return self.features[idx], self.labels[idx]
        return self.features[idx], torch.tensor(-1)  