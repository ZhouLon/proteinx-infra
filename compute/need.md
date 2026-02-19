# Compute 平台需求文档

## 1. 背景与目标
- 目标：实现一个将科研想法与工程实现解耦的训练/实验管理平台。对标 wandb + lightning 的工程落地，但实验管理由本平台自行实现。
- 管理端（Master）已在 `/master` 目录实现并提供可视化；Compute 侧负责训练执行与本地管理。
- 交互约束：Compute 通过 Master IP 对应的 Redis 队列拉取信息；Master 不直接主动与 Compute 交互（无主动推送/远控）。

## 2. 基本约定
- 代码解耦：平台代码位于 `/compute`，业务代码按模块化重构入此目录。
- 包构建：`/compute` 目录最终构建为可安装的 Python 包，对外暴露稳定的模块接口。部署方式：
  - 开发阶段：复制 `/compute` 目录到目标环境，进入该目录执行 `pip install -e .`
  - 发行阶段：直接执行 `pip install proteinx-infra`
- Flag 机制：所有训练/评估参数通过键值对或 JSON 对象传递；需定义统一规范。
- 工作目录：默认 `C:\home\Projects\proteinx_infra\workdir_compute`（可在初始化时配置）。
- 用户范围：当前仅考虑单用户。
- 数据持久化：SQLite（`database.db`）存储元数据与索引，训练产物以文件形式落地。
- 环境管理：采用 `conda` 管控 Python 版本与依赖。
- 指标扩展：用户可自定义 metric，平台提供封装与调用接口。

## 3. 术语
- Experiment：一次训练/评估的抽象，具备唯一 `experiment_id` 与一组 flags。
- Artifact：训练/评估产物（模型权重、日志、曲线、报告等），以文件组织并带索引。
- Queue Message：Redis 队列中的任务元数据（不含大对象，仅引用与参数）。

## 4. 交互与数据流（Compute 侧）
1. Compute 连接 Master 提供的 Redis（按 IP/端口与队列名）拉取任务。
2. 解析 message 中的 `experiment_id`、`flags` 与数据/产物引用（如路径或对象存储 key）。
3. 执行训练/评估，记录日志与指标，写入产物目录并更新本地数据库。
4. 可选：向 Master 后端上报结果引用与状态（由队列消费者或后端调度统一管理），Compute 不依赖 Master 主动回调。

---

## 5. 需求列表

### C-001 Flag 规范与层级
- 描述：定义统一的超参数命名、层级与传递格式，支持 JSON/kv，两者互转；保留扩展字段。
- 约束：
  - 采用层级命名：如 `train.lr`、`train.batch_size`、`model.name`、`data.split`。
  - 所有 flags 序列化为 JSON（UTF-8，无二进制），确保跨进程/跨语言兼容。


### C-002 队列接入（Redis / RQ）
- 描述：Compute 以消费者身份接入 Redis 队列，单并发顺序执行。
- 约束：
  - 连接参数：`REDIS_URL=redis://<MASTER_IP>:6379/0`，`QUEUE_NAME=experiments` 等通过环境变量/配置文件注入。
  - 队列消息仅存元数据与引用：`experiment_id`、`flags`、`payload_ref`。
  - 单 worker 串行消费；后续可扩展为多 worker 或迁移到更强队列（Dramatiq/Celery）。

### C-003 任务生命周期与状态机
- 描述：统一任务状态流转与审计。
- 约束：
  - 状态机：`PENDING → RUNNING → SUCCEEDED/FAILED`，记录 `attempts`、`error`、`trace`、时间戳。
  - 幂等键：`experiment_id`；重复提交按策略覆盖或拒绝（由 flags 中的 `resume/allow_duplicate` 控制）。
  - 本地数据库持久化每次状态变化与摘要（summary 指标）。

### C-004 产物目录结构与索引
- 描述：标准化产物落盘路径与索引，便于前端展示与复现。
- 约束：
  - 目录：`<WORKDIR>/experiments/<experiment_id>/` 下组织：
    - `config/`：`flags.json`、`data_query.json`（查询条件快照）、`pipeline.json`（处理/嵌入/分集配置）
    - `data/`：`selected.csv` 或 `selected.parquet`（筛选得到的目标数据），`transform/`（处理后的中间数据）
    - `embeddings/`：向量化产物（如 `train.pt` / `val.pt` / `test.pt`）
    - `splits/`：分集索引或清单（如 `train_ids.json`）
    - `logs/`：`train.log`、`events/`（结构化事件）
    - `metrics/`：`metrics.jsonl`（分步记录，含层级指标）
    - `ckpts/`：检查点文件（按策略命名与留存）
    - `artifacts/`：评估报告、可视化图表、模型导出等
  - 构建基础 JSON：`experiment.json`，记录 `experiment_id`、`flags`、`created_at`、`updated_at`、`status` 与产物索引摘要。


### C-005 指标与日志记录规范
- 描述：统一指标命名与记录频率，支持用户自定义 metric。
- 约束：
  - 命名层级：`train/loss`、`train/acc`、`val/loss`、`val/acc`。
  - 记录频率：高频指标按步采样或聚合（如每 N 步）；媒体类（图像/直方图）采样上传。
  - 提供 `metrics.register(name, fn)` 接口，封装自定义指标计算并写入标准位置。

### C-006 本地数据库模式（SQLite）
- 描述：本地元数据数据库存储的是数据集与其来源（参考 `tmp/creat_db_from_csv.py` 中的 `sources` 与 `mutations` 结构）。Compute 侧在取到 flags 后，按查询条件筛选目标数据，再依次执行数据处理 → 嵌入 → 分集流程，最后进入模型训练/评估。
- 约束：
  - 表结构（示意，来自数据构建脚本）：
    - `sources(id INTEGER PRIMARY KEY, source_text TEXT UNIQUE NOT NULL, template TEXT NOT NULL)`
    - `mutations(id INTEGER PRIMARY KEY, mutant TEXT NOT NULL, DMS_score REAL, DMS_score_bin TEXT, mut_num INTEGER NOT NULL, source INTEGER NOT NULL REFERENCES sources(id))`
    - 索引：`CREATE INDEX idx_mutations_source ON mutations(source)`
  - 查询流程：
    - 解析 flags 中的筛选条件（如来源 `source_text/template`、`mut_num` 范围、`DMS_score`/`DMS_score_bin` 过滤等）
    - 从本地 SQLite 选出目标数据集记录，生成查询快照与 `selected.csv/parquet`
    - 根据数据处理 flags 执行清洗/归一化/派生字段
    - 根据嵌入 flags 生成向量化数据（写入 `embeddings/`）
    - 根据分集方法 flags 生成 `train/val/test` 划分（写入 `splits/`）
  - 安全与约束：
    - where 构造器：对列名、操作符、值做校验，避免 SQL 注入；路径统一映射到 `WORKDIR`
    - 大对象不进入队列消息；仅存引用或路径

### C-007 训练脚本接口标准（Lightning）
- 描述：统一训练脚本的入口与接口，便于队列调用与参数注入。
- 约束：
  - 入口：`train.py --flags <json>` 或按 argparse 接受常用参数（lr、batch_size、max_epochs、accelerator、devices）。
  - 采用 `LightningModule + DataModule + Trainer` 标准结构；`self.log` 统一记录指标。
  - 支持lightning的功能对应的flag。

### C-008 环境管理与依赖
- 描述：用 conda 管理基础环境，pip 安装项目依赖。
- 约束：
  - 建议：`conda create -n proteinx_infra_compute python=3.12`；`pip install -r requirements.txt`；`pip install -e .`
  - 避免本仓库写入任何密钥；敏感配置经环境变量注入。

### C-009 心跳与资源上报（可选）
- 描述：Compute 以只读/写入的方式在 Redis 维护心跳与资源占用，便于 Master 展示节点状态。
- 约束：
  - 键空间：`nodes/<hostname>/heartbeat`、`nodes/<hostname>/gpu_usage` 等；TTL 控制在线状态。
  - 仅在同网络内部可见；不暴露公网接口。

### C-010 错误处理与重试
- 描述：统一异常处理与重试策略，确保稳定性。
- 约束：
  - 超时与重试：按任务 flags 设置 `timeout/retries`；失败记录 `error`、`trace` 到本地数据库，同样需要返回master的result brpop。
  - 检查点恢复：支持 `ckpt_path` 恢复训练；落盘只保存必要状态，避免 checkpoint 过大。

### C-011 安全约束
- 描述：文件路径、令牌与配置的安全处理。
- 约束：
  - 队列消息不得携带大对象，仅传引用。

### C-012 本机测试与模拟
- 描述：提供本机开发/测试流程，验证 Compute 端到端能力。
- 约束：
  - 启动本地 Redis（或连接 Master 的 Redis），创建示例任务（示例 flags 与 payload_ref）。
  - 提供 `examples/` 目录的最小可运行训练脚本与模拟数据；执行后产物与指标正确落盘与入库。
  - 单用户单并发；完成后可在前端“训练监控”页查看任务状态（通过队列/后端约定接口）。

### C-013 扩展性
- 描述：为未来多 worker、多队列与迁移到更强队列预留接口。
- 约束：
  - 抽象队列客户端接口：`QueueClient.enqueue/dequeue/ack`；当前实现为 Redis/RQ。
  - 抽象存储接口：本地 FS，未来可接 MinIO/S3。
  - 训练接口保持 Lightning 标准，便于策略切换（DDP/FSDP/DeepSpeed）。

### C-014 包构建与发布
- 描述：Compute 平台以可安装的 Python 包形式交付，支持开发模式与发行版安装。
- 约束：
  - 发行名：`proteinx-infra`（Python 导入名以包目录为准）；支持 `pip install proteinx-infra`
  - 开发安装：复制 `/compute` 目录到目标环境，在该目录执行 `pip install -e .`，确保模块接口稳定、版本号管理规范
  - 包内模块结构清晰，避免与业务代码耦合；公共接口文档与示例随包发布

---

## 6. 文档规范与结构
- 本文件采用“编号 + 标题 + 描述 + 约束”的格式；编号以 `C-XYZ` 递增。
- 指标命名与 flags 层级保持一致，便于 Master 侧聚合与前端展示。
- 路径与环境变量在部署文档中统一维护，本文件仅定义接口与约束。
