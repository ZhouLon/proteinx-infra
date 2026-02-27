# Compute 架构说明

## 目标与范围
- 目标：在本地/节点侧提供“训练与实验管理”的可安装平台（对接 Master 管理端），将科研想法与工程实现解耦。
- 范围：命令行入口、工作目录管理、数据选择与预处理、词表编码、训练流程骨架、产物目录规范与可扩展的插件系统。

## 目录结构
- 根目录
  - requirements.txt：基础依赖
  - setup.py：安装与入口点声明
  - ARCHITECTURE.md：本架构文档
  - README.md、need.md：使用与需求说明
- 核心包 infra/
  - __init__.py：工作目录管理与插件自动加载
  - main.py：命令行入口（训练、工作目录）
  - parser.py：参数与实验计划解析
  - training.py：训练流程骨架
  - data.py：SQLite 数据查询与 DataFrame 构建
  - vocab.py：词表处理接口与注册表
  - const.py：IUPAC 字符集常量
  - recoder.py：实验产物目录结构与快照
  - embed.py、metrics.py、visualization.py：扩展占位（待完善）

## 关键组件
- 命令行入口
  - 安装后提供：
    - infra-train → [main.py](file:///c:/home/Projects/proteinx_infra/compute/infra/main.py#L20-L43)
    - infra-wkdir → [main.py](file:///c:/home/Projects/proteinx_infra/compute/infra/main.py#L45-L67)
  - 入口点声明见 [setup.py](file:///c:/home/Projects/proteinx_infra/compute/setup.py#L11-L16)
- 工作目录与插件系统
  - 工作目录配置与持久化：见 [__init__.py](file:///c:/home/Projects/proteinx_infra/compute/infra/__init__.py#L14-L43)
  - 强制校验与获取：见 [require_workdir](file:///c:/home/Projects/proteinx_infra/compute/infra/__init__.py#L55-L63)
  - 插件自动加载：在工作目录下的 model/embed/metrics/vocab 目录中的 .py 会被动态导入到 infra_ext.* 命名空间
    - 实现见 [_auto_load_plugins](file:///c:/home/Projects/proteinx_infra/compute/infra/__init__.py#L81-L93)
- 参数解析与实验计划
  - 训练参数解析：从 CLI 读取实验计划 JSON 并合并到 args，见 [TrainParser](file:///c:/home/Projects/proteinx_infra/compute/infra/parser.py#L7-L20)
  - 校验需求：实验计划必须包含 data 与 model 字段，见 [parser.py](file:///c:/home/Projects/proteinx_infra/compute/infra/parser.py#L41-L51)
  - 工作目录 CLI：支持 --get/--set/--clear，见 [WorkdirParser](file:///c:/home/Projects/proteinx_infra/compute/infra/parser.py#L54-L79)
- 数据访问与预处理
  - SQLite 访问：自动解析目标表、校验列与构造 where 子句，见 [data.py](file:///c:/home/Projects/proteinx_infra/compute/infra/data.py#L12-L33) 与 [data.py](file:///c:/home/Projects/proteinx_infra/compute/infra/data.py#L34-L61)
  - 记录查询与联表：默认表为 mutations，联接 sources 以拿到 source_text，见 [query_records](file:///c:/home/Projects/proteinx_infra/compute/infra/data.py#L62-L90)
  - DataFrame 构建：根据 template 与 mutant 生成突变序列文本与编码，见 [build_dataframe](file:///c:/home/Projects/proteinx_infra/compute/infra/data.py#L91-L138)
- 词表与编码
  - 词表处理接口：见 [BaseVocabProcessor](file:///c:/home/Projects/proteinx_infra/compute/infra/vocab.py#L4-L26)
  - 注册与获取：register_vocab / get_vocab_processor，见 [vocab.py](file:///c:/home/Projects/proteinx_infra/compute/infra/vocab.py#L28-L37)
  - IUPAC 常量：见 [const.py](file:///c:/home/Projects/proteinx_infra/compute/infra/const.py)
- 模型与注册表
  - 基类：ProteinModel，见 [model.py](file:///c:/home/Projects/proteinx_infra/compute/infra/model.py)
  - 任务模型管理：ModelSpec / Registry（占位），见 [registry.py](file:///c:/home/Projects/proteinx_infra/compute/infra/registry.py)
- 训练流程骨架
  - 入口：infra-train → 校验工作目录 → 解析实验计划 → 根据函数签名组织参数 → 调用 run_train
  - 执行：查询数据、构建 DataFrame、日志预览；训练与评估待接入，见 [training.py](file:///c:/home/Projects/proteinx_infra/compute/infra/training.py)
- 实验产物目录
  - 目录结构封装与创建：见 [ExperimentRecorder.create_dirs](file:///c:/home/Projects/proteinx_infra/compute/infra/recoder.py#L10-L31)
  - 约定的产物：exp_plan.json、training/、model.pth、labels.npz、metrics.json、visualization/

## 数据与控制流
- CLI 执行（infra-train）
  - 解析实验计划 JSON（包含 data/model/embeddings/split/train.* 等 flags）
  - 校验并加载工作目录，自动加载插件
  - 使用 data.where 过滤从 SQLite 选出的记录，构造 DataFrame
  - 通过 vocab 编码序列，生成固定长度的 ID 序列
  - 执行训练与评估（Lightning 计划接入），写出产物与指标
- CLI 执行（infra-wkdir）
  - 查询/设置/清空当前节点工作目录，并触发插件加载

## 配置与 Flags
- flags 采用“层级命名”与 JSON 表示，示例键：
  - train.lr、train.batch_size、train.max_epochs
  - model.name、data.dataset、split.strategy、embeddings.name
- 入口约定：infra-train <exp_plan_path>，exp_plan JSON 中包含上述层级键

## 本地数据库模式（假设）
- 数据库由外部构建脚本生成，表结构示意：
  - sources(id, source_text, template)
  - mutations(id, mutant, DMS_score, DMS_score_bin, mut_num, source REFERENCES sources(id))
- 训练侧按 flags 构造查询，避免注入与无效列，参考 [data.py](file:///c:/home/Projects/proteinx_infra/compute/infra/data.py)

## 产物目录结构（建议）
- <WORKDIR>/experiments/<experiment_id>/
  - config/：flags 与查询快照
  - data/：selected.csv 或 parquet
  - embeddings/：train/val/test 的向量化结果
  - splits/：分集清单
  - logs/：训练日志与结构化事件
  - metrics/：指标 JSONL
  - ckpts/：检查点
  - artifacts/：报告与可视化
- 当前实现的最小集合：training/、model.pth、labels.npz、metrics.json、visualization/，参考 [recoder.py](file:///c:/home/Projects/proteinx_infra/compute/infra/recoder.py)

## 日志与调试
- 统一日志格式初始化于入口脚本，支持 --debug 切换全局级别，见 [main.py](file:///c:/home/Projects/proteinx_infra/compute/infra/main.py#L11-L16)
- data 模块提供查询信息与样本预览的调试日志

## 扩展点与约定
- 插件扩展（工作目录）
  - 在 <WORKDIR>/vocab 下编写 .py 模块，调用 register_vocab("IUPAC", factory) 即可扩展词表
  - 在 <WORKDIR>/model、embed、metrics 下提供模块以扩展模型、嵌入与指标
  - 模块会被自动导入到 infra_ext.* 命名空间（无需改动主包）
- 训练框架
  - 依赖中已包含 lightning/torch/pandas/scikit-learn 等，见 [requirements.txt](file:///c:/home/Projects/proteinx_infra/compute/requirements.txt)
  - 后续将以 LightningModule/DataModule/Trainer 标准化训练流程与指标记录

## 待完善事项
- 训练与评估：接入 Lightning，统一指标记录与检查点策略
- 嵌入/指标/可视化：完善 embed.py、metrics.py、visualization.py 的接口与默认实现
- Registry：打通任务到模型的映射与选择
- 实验记录：在 run_train 中集成 ExperimentRecorder，落盘 flags 与数据快照
- 队列接入：按 need.md 的约定接入 Redis/RQ，统一状态机与幂等策略
- 心跳与资源上报：节点侧只读/写入心跳与资源占用（可选）
- 安全与异常：路径与 SQL 进一步约束，失败重试与错误追踪

## 安装与运行
- 安装（开发模式）：在 compute 目录执行
  - pip install -r requirements.txt
  - pip install -e .
- 使用
  - infra-wkdir --set <PATH> ｜ --get ｜ --clear
  - infra-train <path/to/exp_plan.json>
