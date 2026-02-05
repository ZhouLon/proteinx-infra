import torch
import torch.nn as nn


class SimpleRegressor(nn.Module):
    """简单的回归/回归式评分网络。
    以序列嵌入的平均表示为输入，输出单个标量。
    """
    def __init__(self, input_dim: int, hidden_dims=(128, 64), dropout=0.1):
        super().__init__()
        layers = []
        prev = input_dim
        for h in hidden_dims:
            layers.append(nn.Linear(prev, h))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev = h
        layers.append(nn.Linear(prev, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


if __name__ == '__main__':
    m = SimpleRegressor(27)
    x = torch.randn(4, 27)
    y = m(x)
    print(y.shape)
