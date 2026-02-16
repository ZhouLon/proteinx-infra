# Weights & Biases（W&B）极简使用教程

## 1. W&B 是什么
- 面向机器学习/深度学习的实验跟踪与协作平台
- 记录训练过程中的指标、超参数、模型产物与系统资源，生成可交互的可视化与报告
- 提供团队协作、版本管理与复现实验的能力

## 2. 有什么用
- 实验跟踪：自动记录 loss/accuracy 等指标，随时间绘图
- 配置管理：保存每次训练的超参数（config）
- 可视化与对比：支持多次运行（run）之间的对比与筛选
- 超参搜索：Sweeps 自动化搜索与网格/贝叶斯优化
- 产物管理：Artifacts 存储与版本化数据/模型文件
- 报告与分享：生成交互式报告，支持团队协作

## 3. 核心概念
- Project：项目空间（如 proteinx-experiments）
- Entity：组织/用户（团队名或用户名）
- Run：一次训练执行实例（含指标、config、日志）
- Config：超参数字典（如学习率、batch size）
- Summary：每次 run 的最终统计（如最佳指标）
- Artifacts：文件/数据集的版本管理与依赖图
- Sweeps：超参搜索任务集合

## 4. 快速开始
- 安装：`pip install wandb`
- 登录：
  - 命令行：`wandb login`（按提示输入 API Key）
  - 或环境变量：`WANDB_API_KEY=xxxx`
- 最小示例（PyTorch/通用 Python）：

```python
import wandb, random, time

wandb.init(project="proteinx-experiments", entity="your-team", config={
    "lr": 1e-3,
    "batch_size": 64,
    "model": "resnet18",
})

for step in range(100):
    loss = 1.0 / (step + 1) + random.random() * 0.01
    acc = step / 100.0 + random.random() * 0.01
    wandb.log({"train/loss": loss, "train/acc": acc}, step=step)
    time.sleep(0.05)

wandb.finish()
```

## 5. 与 PyTorch Lightning 集成

```python
import wandb
from pytorch_lightning.loggers import WandbLogger
from pytorch_lightning import Trainer

wandb_logger = WandbLogger(project="proteinx-experiments", entity="your-team")
trainer = Trainer(max_epochs=10, logger=wandb_logger)
# trainer.fit(model, datamodule=dm)
```

- Lightning 自动将训练指标（loss、metrics）写入 W&B
- 可在 UI 上对比不同 run、下载 artifacts、生成报告

## 6. 记录丰富数据（图片/直方图/表格）

```python
import wandb
import numpy as np

# 图片
image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
wandb.log({"samples/image": wandb.Image(image)}, step=10)

# 直方图
values = np.random.randn(1000)
wandb.log({"dist/weights": wandb.Histogram(values)}, step=20)

# 表格
table = wandb.Table(columns=["id", "score"])
for i in range(5):
    table.add_data(i, np.random.rand())
wandb.log({"eval/top5": table}, step=30)
```

## 7. 超参搜索（Sweeps）
- 定义 sweep 配置（YAML/字典），指定搜索空间与目标指标
- 命令：`wandb sweep sweep.yaml`；工作进程：`wandb agent <sweep_id>`

```yaml
program: train.py
method: bayes
metric:
  name: val/accuracy
  goal: maximize
parameters:
  lr:
    min: 1e-5
    max: 1e-2
  batch_size:
    values: [32, 64, 128]
```

## 8. 产物管理（Artifacts）
- 保存/加载模型、数据集等文件，建立依赖图与版本

```python
import wandb
run = wandb.init(project="proteinx-experiments")
artifact = wandb.Artifact("best-model", type="model")
artifact.add_file("checkpoints/best.pth")
run.log_artifact(artifact)
run.finish()
```

## 9. 运行模式与环境变量
- 常用环境变量：
  - `WANDB_PROJECT`、`WANDB_ENTITY`：默认项目与组织
  - `WANDB_MODE=offline`：离线模式（无网络时使用）
  - `WANDB_RUN_ID`：指定/恢复某次 run
- 离线与重同步：
  - 离线记录完成后，运行：`wandb sync <dir_or_run>` 将本地数据推送到云端

## 10. 最佳实践
- 保密：API Key 通过环境变量注入，避免写入代码或仓库
- 命名与层级：指标名使用层级（如 train/loss、val/acc）
- 采样频率：对高频指标做采样或聚合，避免过多日志压力
- 结构化记录：使用 Table/Artifacts 管理样本与模型文件
- 组与标签：使用 group 与 tags 对 run 分类（如模型/数据版本）

## 11. 常见问题
- 网络隔离/代理：设置系统代理或使用离线模式；完成后 `wandb sync`
- 权限错误：检查 Entity/Project 是否可写，团队权限是否正确
- 速率限制：避免每步大量媒体上传，使用采样/间隔记录
- 恢复运行：`WANDB_RUN_ID` 与 `resume="allow"` 配合以断点续传

## 12. 在 ProteinX 项目中的建议接入
- 训练任务集成 WandbLogger，自动记录指标与系统资源
- 将模型权重与评估结果作为 Artifacts 上传，便于版本化与复现
- 将 run_id 与任务 ID 关联，前端“训练监控”页可跳转到 W&B 详情
- 在 Worker 启动脚本里注入 `WANDB_PROJECT`、`WANDB_ENTITY`，按项目进行归档

