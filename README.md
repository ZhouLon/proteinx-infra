# ProteinX Infra

**平台是什么**
- 面向科研与工程的实验管理与训练执行平台，强调“科研想法 ↔ 工程实现”的解耦
- 管理端（Master）负责项目/数据/任务/监控与可视化；计算端（Compute）负责数据管线与训练执行
- 采用自托管的安全策略；通过 Redis 队列传递任务元数据，避免直接远控

**目录结构**
- 管理端：[master](file:///c:/home/Projects/proteinx_infra/master)（前后端分离）
  - 后端 FastAPI（认证、安全、项目/数据/任务 API）[backend/ARCHITECTURE.md](./master/backend/ARCHITECTURE.md)
  - 前端 React + Vite + Ant Design（控制台 UI）[frontend/ARCHITECTURE.md](./master/frontend/ARCHITECTURE.md)
  - 队列 RQ + Redis（单并发、顺序执行）[queue/ARCHITECTURE.md](./master/queue/ARCHITECTURE.md)
- 计算端：[compute]
  - 库代码（infra/*）：配置、flags、SQLite 查询、数据管线、产物管理、嵌入、数据集
  - 架构说明：[ARCHITECTURE.md](./compute/ARCHITECTURE.md)


**主要能力**
- 项目与数据管理、认证与安全、任务队列与状态跟踪
- 数据筛选 → 处理 → 嵌入 → 分集 → 训练/评估 的标准化管线
- 实验目录与产物归档、指标日志（metrics.jsonl）、检查点与报告

**部署方法**
- 管理端（容器化部署）
  - 配置 .env（WORKDIR_HOST、WORKDIR_CONTAINER、后端端口等）
  - 执行 docker compose up -d（前端容器反代到后端容器；Redis 与队列消费者在同网络）
- 计算端（两种安装方式）
  - 开发安装：复制 /compute 到目标环境，进入该目录执行
    - pip install -e .
  - 发行安装：
    - pip install proteinx-infra





