# Weights & Biases（W&B）使用与总结

## 1. W&B 是什么
- 面向机器学习/深度学习的实验跟踪与协作平台
- 通过少量代码记录训练指标、超参数、产物与环境信息
- 在交互式仪表盘中查看、对比与分享结果，并支持程序化访问 API

## 2. 有什么用（价值总结）
- 实验跟踪：loss、accuracy 等随时间可视化，自动生成图表
- 超参数管理：配置集中化，便于复现实验与筛选对比
- 产物版本：Artifacts 管理数据集与模型文件依赖图与历史版本
- 超参搜索：Sweeps 支持网格/贝叶斯优化，统一查看搜索结果
- 团队协作：项目/组织维度的共享、标签与报告（可交互）

## 3. 核心概念对照
- Project（项目）：一组可比较的实验集合
- Entity（组织/用户）：归属的团队或个人空间
- Run（运行）：一次训练执行实例，包含指标、config、日志
- Config（配置）：用于复现的超参数字典（如 lr、batch_size）
- Summary（摘要）：每个 run 的最终统计（最佳指标等）
- Artifacts（产物）：数据/模型文件的版本化与依赖跟踪
- Sweeps（搜索）：超参数搜索任务集合与其结果面板

## 4. 工作原理（来自 /tmp/docs/wandb 的要点）
1) 初始化 Run：`wandb.init(project="...", entity="...")`  
2) 捕获配置：`run.config = {...}` 或 `wandb.init(config={...})`  
3) 训练循环中记录：`run.log({"loss": loss, "acc": acc}, step=...)`  
4) 保存产物：`run.log_artifact(...)`（模型权重、数据文件等）  
完成后可在仪表盘查看多次 Run 的指标曲线与并行坐标等图表，并支持以标签、配置列进行筛选与对比。

## 5. 快速开始（Python）
```python
import wandb, time, random

with wandb.init(project="proteinx-experiments", entity="your-team", config={
    "lr": 1e-3, "batch_size": 64, "model": "resnet18"
}) as run:
    for step in range(100):
        loss = 1.0 / (step + 1) + random.random() * 0.01
        acc = step / 100.0 + random.random() * 0.01
        run.log({"train/loss": loss, "train/acc": acc}, step=step)
        time.sleep(0.05)
```
登录方式：命令行 `wandb login`（输入 API Key）或设置环境变量 `WANDB_API_KEY=...`。  

## 6. 配置管理（Config）
- 初始化时传入：`wandb.init(config={"epochs":100,"lr":0.001})`
- 运行中更新：`run.config["lr"] = 0.001`
- 约定：使用下划线或中划线命名，避免 `.` 带来的层级歧义；访问嵌套键用字典语法 `run.config["key"]`。

## 7. 指标与丰富数据记录
- 标量：`run.log({"loss":loss,"acc":acc}, step=step)`
- 图片：`wandb.Image(np_array)`
- 直方图：`wandb.Histogram(values)`
- 表格：`wandb.Table(columns=[...]); table.add_data(...); run.log({"eval/table": table})`

## 8. 产物版本（Artifacts）
```python
with wandb.init(project="proteinx-experiments") as run:
    # 保存模型文件/目录为版本化产物
    run.log_artifact("checkpoints/best.pth", name="best-model", type="model")
```
在 UI 中可查看依赖关系、版本历史与下载链接，适合管理数据集与模型产物。

## 9. 超参搜索（Sweeps）
定义搜索空间与目标指标（YAML/字典），命令：`wandb sweep sweep.yaml`，然后运行 Agent：`wandb agent <sweep_id>`。
```yaml
program: train.py
method: bayes
metric: { name: val/accuracy, goal: maximize }
parameters:
  lr: { min: 1e-5, max: 1e-2 }
  batch_size: { values: [32, 64, 128] }
```

## 10. 可视化与仪表盘（来自 /tmp/docs/wandb 的要点）
- 运行对比：支持并行坐标、参数重要性、曲线叠加等图表
- 交互筛选：按标签、配置列、分组进行过滤与聚合
- 报告：将关键图表组合为可共享的交互式文档

## 11. 运行模式与环境变量
- `WANDB_PROJECT`、`WANDB_ENTITY`：默认项目与组织
- `WANDB_MODE=offline`：离线记录（网络不可用时），完成后 `wandb sync` 同步
- `WANDB_RUN_ID`：指定/恢复某次 run（断点续传）

## 12. 最佳实践（综合 /tmp/docs/wandb 与经验）
- 结构化命名：指标层级（如 `train/loss`、`val/acc`），便于分组与筛选
- 合理频率：高频指标按间隔/采样记录，降低日志与上传压力
- 完整元数据：config 中记录数据版本、架构、随机种子、重要开关
- 标签与备注：用于分组与筛选（baseline、paperX、ablation 等）
- 结束运行：`with wandb.init(...)` 或显式 `run.finish()`，确保上传完成

## 13. 常见问题与建议
- 网络/代理：离线模式 + `wandb sync`；或配置系统代理
- 权限：检查 Entity/Project 可写权限与团队设置
- 速率限制：避免每步上传大量媒体；媒体使用采样或批量
- 恢复：`WANDB_RUN_ID` 与 `resume="allow"` 配合以继续记录

## 14. 在 ProteinX 项目中的接入建议
- Worker 训练脚本集成 W&B（或 Lightning 的 WandbLogger），记录指标与系统资源
- 使用 Artifacts 管理模型权重与评估结果，形成版本化产物
- 前端训练监控页可加入跳转到 W&B 的 run 链接（run_id 对齐）
- 在节点启动脚本中注入 `WANDB_PROJECT`、`WANDB_ENTITY` 与 API Key

## 15. 小结
- W&B 以“Run + Config + Log + Artifacts + Sweeps”为核心，覆盖从训练记录到产物版本与搜索的完整闭环
- 对于团队协作与复现实验尤为关键：统一视图、强可视化、标准化记录与分享能力

