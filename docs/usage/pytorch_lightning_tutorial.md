# PyTorch Lightning 全面教程

## 1. 为什么选择 Lightning
- 结构清晰：将模型逻辑（LightningModule）与数据加载（DataModule）、训练流程（Trainer）解耦
- 可复现与工程化：统一日志、检查点、回调，减少样板代码
- 硬件无关：一行配置切换 CPU/GPU/多机分布式/Mixed Precision
- 与生态良好集成：W&B、TensorBoard、MLFlow、Ray 等

## 2. 安装
- 安装 PyTorch（根据 CUDA 版本选择轮子）：参考 https://pytorch.org/get-started/locally/
- 安装 PyTorch Lightning：

```bash
pip install lightning
```

- 常用配套：
```bash
pip install torch torchvision torchaudio  # 依据项目需要
pip install tensorboard                   # 可选：本地可视化
pip install wandb                         # 可选：云端实验跟踪
```

## 3. 最小工作示例
### 3.1 定义 LightningModule
```python
import torch
from torch import nn
from torch.nn import functional as F
import pytorch_lightning as pl

class LitClassifier(pl.LightningModule):
    def __init__(self, lr: float = 1e-3, num_classes: int = 10):
        super().__init__()
        self.save_hyperparameters()  # 自动保存超参到 checkpoint
        self.model = nn.Sequential(
            nn.Flatten(),
            nn.Linear(28 * 28, 256),
            nn.ReLU(),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = F.cross_entropy(logits, y)
        acc = (logits.argmax(dim=1) == y).float().mean()
        self.log("train/loss", loss, prog_bar=True)
        self.log("train/acc", acc, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = F.cross_entropy(logits, y)
        acc = (logits.argmax(dim=1) == y).float().mean()
        self.log("val/loss", loss, prog_bar=True)
        self.log("val/acc", acc, prog_bar=True)

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.lr)
```

### 3.2 定义 DataModule（数据加载）
```python
from torch.utils.data import DataLoader, random_split
from torchvision import transforms
from torchvision.datasets import MNIST

class MNISTDataModule(pl.LightningDataModule):
    def __init__(self, data_dir: str = "./data", batch_size: int = 64):
        super().__init__()
        self.data_dir = data_dir
        self.batch_size = batch_size
        self.transform = transforms.Compose([transforms.ToTensor()])

    def prepare_data(self):
        MNIST(self.data_dir, train=True, download=True)
        MNIST(self.data_dir, train=False, download=True)

    def setup(self, stage: str = None):
        mnist_full = MNIST(self.data_dir, train=True, transform=self.transform)
        self.mnist_train, self.mnist_val = random_split(mnist_full, [55000, 5000])
        self.mnist_test = MNIST(self.data_dir, train=False, transform=self.transform)

    def train_dataloader(self):
        return DataLoader(self.mnist_train, batch_size=self.batch_size, shuffle=True, num_workers=4)

    def val_dataloader(self):
        return DataLoader(self.mnist_val, batch_size=self.batch_size, num_workers=4)

    def test_dataloader(self):
        return DataLoader(self.mnist_test, batch_size=self.batch_size, num_workers=4)
```

### 3.3 训练
```python
if __name__ == "__main__":
    dm = MNISTDataModule(batch_size=64)
    model = LitClassifier(lr=1e-3)
    trainer = pl.Trainer(max_epochs=5)
    trainer.fit(model, datamodule=dm)
    trainer.test(model, datamodule=dm)
```

## 4. Lightning 关键组件
### 4.1 LightningModule 标准接口
- forward：前向传播（推理/导出）
- training_step / validation_step / test_step：每阶段的单步逻辑
- configure_optimizers：返回优化器与（可选）LR 调度器
- 对齐日志规范：统一使用 `self.log("split/metric", value)`，便于对比

### 4.2 DataModule 职责
- prepare_data：一次性下载/预处理（单进程，避免重复）
- setup：划分数据集与构建 Dataset 实例（每进程执行）
- *dataloader：返回各阶段的 DataLoader（控制 batch_size、num_workers、shuffle）

### 4.3 回调（Callbacks）
- ModelCheckpoint：按指标/周期保存权重
- EarlyStopping：早停，避免过拟合与浪费算力
- LearningRateMonitor：记录学习率，便于排查训练问题

```python
from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping, LearningRateMonitor

checkpoint_cb = ModelCheckpoint(
    monitor="val/acc",
    mode="max",
    filename="mnist-{epoch:02d}-{val_acc:.4f}",
    save_top_k=3,
)
earlystop_cb = EarlyStopping(monitor="val/acc", mode="max", patience=5)
lrmon_cb = LearningRateMonitor(logging_interval="step")

trainer = pl.Trainer(
    max_epochs=20,
    callbacks=[checkpoint_cb, earlystop_cb, lrmon_cb],
)
```

## 5. 日志与实验跟踪
- 内置 `self.log` 支持在 step/epoch 维度记录标量、控制进度条显示
- 集成外部 Logger（如 W&B、TensorBoard、MLFlow）统一管理实验

```python
from pytorch_lightning.loggers import WandbLogger, TensorBoardLogger

wandb_logger = WandbLogger(project="proteinx-experiments", entity="your-team")
tb_logger = TensorBoardLogger(save_dir=".", name="tb_logs")

trainer = pl.Trainer(
    logger=[wandb_logger, tb_logger],
    max_epochs=10,
)
```

## 6. 超参数与配置管理
- 推荐用 argparse/YAML 管理训练配置，Lightning 会将 `self.save_hyperparameters()` 自动写入 checkpoint
- 统一指标命名（如 `train/loss`、`val/acc`）与层级，便于筛选与对比

```python
import argparse

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--batch_size", type=int, default=64)
    p.add_argument("--max_epochs", type=int, default=10)
    p.add_argument("--accelerator", type=str, default="auto")  # cpu/gpu/mps
    p.add_argument("--devices", type=str, default="auto")      # 数量或 auto
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    dm = MNISTDataModule(batch_size=args.batch_size)
    model = LitClassifier(lr=args.lr)
    trainer = pl.Trainer(
        max_epochs=args.max_epochs,
        accelerator=args.accelerator,
        devices=args.devices,
        precision="16-mixed",  # 可选：提升训练吞吐
    )
    trainer.fit(model, dm)
```

## 7. 训练加速与硬件配置
- accelerator：选择 "cpu" / "gpu" / "mps" / "tpu" / "auto"
- devices：整数或 "auto"（自动选择所有可用设备）
- precision：支持 "16-mixed"、"bf16-mixed"、"32-true" 等
- strategy：分布式策略，如 "ddp"、"fsdp"、"deepspeed"
- gradient_clip_val：梯度裁剪，稳定训练
- accumulate_grad_batches：梯度累积实现大 batch

```python
trainer = pl.Trainer(
    accelerator="gpu",
    devices="auto",
    strategy="ddp",
    precision="16-mixed",
    accumulate_grad_batches=2,
    gradient_clip_val=1.0,
)
```

## 8. 多机多卡分布式
- 启用 DDP：`strategy="ddp"`，`devices=N` 表示单机 N 卡
- 多机训练：配合 `num_nodes=M`，由集群启动器（如 Slurm/K8S）分配
- 进程环境：Lightning 自动设置 rank/world_size 与随机种子

```python
trainer = pl.Trainer(
    accelerator="gpu",
    devices=8,        # 单机 8 卡
    num_nodes=2,      # 两台机器
    strategy="ddp",
)
```

## 9. 检查点与恢复
- 自动保存：ModelCheckpoint 回调按指标/步数保存
- 手动恢复：`trainer.fit(model, ckpt_path="path/to/ckpt")`
- 推理加载：`LitClassifier.load_from_checkpoint("ckpt.ckpt")`

```python
ckpt_model = LitClassifier.load_from_checkpoint("checkpoints/best.ckpt")
ckpt_model.eval()
```

## 10. 常用训练技巧
- `pl.seed_everything(42)`：统一随机种子，便于复现
- `detect_anomaly=True`：定位 NaN/Inf 的梯度来源
- `benchmark=True`：固定输入维度时加速 cuDNN 算子选择
- `limit_train_batches / limit_val_batches`：调试时缩小数据量

```python
trainer = pl.Trainer(
    max_epochs=10,
    detect_anomaly=True,
    benchmark=True,
    limit_train_batches=0.2,
    limit_val_batches=0.2,
)
```

## 11. 与 W&B/TensorBoard 集成建议
- 指标命名使用层级（如 `train/loss`、`val/acc`）
- 高频指标控制记录频率；图片/直方图采样上传
- 分组/标签（group/tags）区分不同数据/模型版本
- 详见本项目的 W&B 指南文档

## 12. 在 ProteinX 项目中的建议接入
- 统一采用 LightningModule + DataModule 组织训练代码
- 默认集成 WandbLogger，记录指标与系统资源；与“训练监控”联动
- 使用 ModelCheckpoint 将权重与评估结果作为 Artifacts 归档
- 通过命令行 flags 管理超参；`self.save_hyperparameters()` 自动写入
- 硬件配置采用 `accelerator="gpu"`, `devices="auto"`；集群下使用 DDP
- 训练脚本结构建议：

```python
# train.py
import pytorch_lightning as pl
from pytorch_lightning.loggers import WandbLogger
from mypkg.data import MyDataModule
from mypkg.model import MyLightningModule
from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping

def main():
    pl.seed_everything(42)
    dm = MyDataModule(...)
    model = MyLightningModule(...)
    logger = WandbLogger(project="proteinx-experiments", entity="your-team")
    callbacks = [
        ModelCheckpoint(monitor="val/metric", mode="max", save_top_k=3),
        EarlyStopping(monitor="val/metric", mode="max", patience=5),
    ]
    trainer = pl.Trainer(
        accelerator="gpu",
        devices="auto",
        precision="16-mixed",
        max_epochs=50,
        logger=logger,
        callbacks=callbacks,
    )
    trainer.fit(model, dm)

if __name__ == "__main__":
    main()
```

## 13. 常见问题与排查
- OOM（显存不足）：减小 batch_size，启用混合精度，使用梯度累积
- DDP 进程挂起：确认数据加载器 `num_workers` 设置与随机种子；避免在 `__init__` 里做 I/O
- 日志过慢：降低记录频率，对图片/表格采样上传
- Windows 系统编译问题：尽量使用官方二进制轮子，避免本地编译
- Checkpoint 过大：只保存必要状态，禁用不必要的缓存（如大型字典）

## 14. 参考与延伸
- 官方文档：https://lightning.ai/docs/pytorch/latest/
- PyTorch 安装与 CUDA 对应版本：https://pytorch.org/get-started/locally/
- W&B 集成参考：项目内 W&B 指南

---

本教程面向工程落地与团队协作，建议在本仓库内统一采用 LightningModule/DataModule/Trainer + Logger/Callback 的标准化结构，便于维护、调试与复现。
