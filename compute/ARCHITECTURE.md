# ProteinX Compute 平台代码架构

## 1. 总览
- 目标：在本机/工作节点上执行“数据筛选 → 数据处理 → 嵌入 → 分集 → 训练/评估”，并标准化实验目录与产物。
- 位置：源码位于 `/compute`。运行脚本与配置文件位于工作目录（默认 `C:\home\Projects\proteinx_infra\workdir_compute`）。
- 交互：通过 flags（JSON/kv）驱动流程；从本地 SQLite 元数据库检索数据集；产物落盘于工作目录。

## 2. 目录结构（源码）
```
compute/
├── infra/
│   ├── artifacts.py      # 实验目录与快照管理
│   ├── config.py         # 工作目录与元数据库路径
│   ├── db/
│   │   ├── __init__.py   # 对外导出
│   │   └── db.py         # SQLite 查询构造与执行
│   ├── flags.py          # flags 读写与 experiment_id 工具
│   ├── pipeline.py       # 数据管线（查询→嵌入→分集→落盘）
│   └── data/
│       ├── dataset.py    # 数据集封装（Tensor）
│       ├── embedding/
│       │   └── embedding.py # 简易嵌入接口（onehot/vocab）
│       └── load_data.py  # 表格数据加载（示例）
├── need.md               # 需求文档（编号化约束与流程）
├── requirements.txt
└── setup.py              # 包构建配置（发行名 proteinx-infra）
```

## 3. 目录结构（工作目录）
```
workdir_compute/
├── configs/
│   └── flags.json             # 运行配置（示例见 flags_example.json）
├── scripts/
│   └── train.py               # 训练入口脚本（调用库）
└── experiments/<experiment_id>/
    ├── config/                # flags/data_query/pipeline 快照
    ├── data/                  # selected.csv|parquet 与 transform/
    ├── embeddings/            # 向量化产物（data.pt 等）
    ├── splits/                # train/val/test 划分
    ├── logs/                  # 文本与事件日志
    ├── metrics/               # metrics.jsonl（分步记录）
    ├── ckpts/                 # 检查点
    └── artifacts/             # 报告与导出文件
```

## 4. 核心数据流
1) 解析 flags → 保存快照（config/flags.json、config/data_query.json、config/pipeline.json）  
2) 从 SQLite（sources/mutations）按 flags 查询 → 输出 selected.csv|parquet  
3) 执行嵌入（如 onehot/vocab）→ 保存到 embeddings/data.pt  
4) 执行分集（ratio 或其他方法）→ 保存 train/val/test_ids.json  
5) 写入 metrics.jsonl 与 experiment.json（记录状态与摘要）  
6) 训练入口（Lightning）读取 embeddings 与标签，记录训练/验证指标与 checkpoint

## 5. SQLite 元数据库
- 表结构参考 `tmp/creat_db_from_csv.py`：`sources` 与 `mutations`，并建立 `idx_mutations_source`。
- 查询由 `infra/db/QueryBuilder` 构造 where 子句；安全校验列名与操作符；仅支持白名单。

## 6. Flags 约定（示例）
```json
{
  "experiment_id": "exp_demo_001",
  "data": {
    "format": "csv",
    "seq_field": "mutant",
    "query": [
      { "table": "mutations", "column": "mut_num", "op": ">=", "value": 1 },
      { "table": "mutations", "column": "DMS_score_bin", "op": "IN", "value": ["A", "B"] }
    ]
  },
  "embeddings": { "type": "onehot" },
  "split": { "method": "ratio", "train_ratio": 0.8, "val_ratio": 0.1 },
  "train.lr": 0.001,
  "train.batch_size": 32,
  "train.max_epochs": 5
}
```

## 7. 训练入口
- 工作目录中的 `scripts/train.py` 调用库的 `infra.pipeline.run(flags)` 完成数据准备，然后用 Lightning 训练最小模型。
- 产物与日志统一落入 `experiments/<experiment_id>/`。

## 8. 扩展与约束
- 队列对接：后续可在工作目录新增队列脚本，从 Redis 拉取任务并复用 pipeline 与训练入口。
- 嵌入与处理：可按 `need.md` 的 C-004/C-006/C-007 扩展更丰富的策略与流水线。
- 安全：仅允许白名单列与操作符；路径统一映射到 WORKDIR；队列消息只传引用不传大对象。
