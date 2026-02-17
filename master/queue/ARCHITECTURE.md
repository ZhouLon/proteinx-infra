# ProteinX Infra Master 队列架构（RQ + Redis）

## 1. 概览
- 目标：为 Master 管理端提供可靠、简洁的队列与调度，满足“单并发、顺序执行、关机后不丢任务、结果回传”的需求。
- 选型：RQ（Redis Queue）。队列数据存储在 Redis（持久卷 + AOF），消费者通过 `rq worker` 执行任务。
- 形态：前后端分容器，新增 Redis 服务与“队列消费者”容器，在同一网络内通信。


## 2. 选型与理由
- 简单：API 极简，Python 生态友好，学习成本低。
- 持久：Redis 开启 AOF（appendonly yes）与持久卷，关机后队列不丢失。
- 单并发契合：单 worker 串行消费，贴合“每次仅运行一个任务”的业务约束。
- 取舍：不提供复杂工作流编排；如未来需要可迁移至 Dramatiq/Celery。

## 3. 组件与职责
- 后端（FastAPI，producer）
  - 暴露 API 接口供前端/管理端创建任务（POST /api/jobs）。
  - 使用 RQ 客户端将任务写入 Redis 队列（`Queue('experiments', connection=Redis(...))`）。
  - 提供结果回调/状态查询接口（例如：POST /api/jobs/{id}/result，GET /api/jobs/{id}）。
  - 参考后端架构文档的接口清单与状态设计，见[backend/ARCHITECTURE.md](file:///c:/home/Projects/proteinx_infra/master/backend/ARCHITECTURE.md#L64-L116)。
- 队列消费者（queue-worker，consumer）
  - 运行 `rq worker`，连接 Redis，并监听目标队列（如 `experiments`）。
  - 并发设为 1（单工作者，默认一个进程一个任务）。
  - 执行任务后将结果写入外部存储（对象存储/DB），并调用后端回调接口。
- Redis（队列存储）
  - 配置持久化：`appendonly yes`，`appendfsync everysec`。
  - 通过 Compose 将 Redis 数据目录挂载到宿主机持久卷。

## 4. 数据流与状态
1. 前端调用后端创建任务：POST `/api/jobs`，提交 experiment_id、flags、payload_ref（对象存储/DB 引用）。
2. 后端入队：构造任务元数据并通过 RQ 推送到 Redis 队列。
3. 消费者取出任务并执行：
   - 加载 payload 引用 → 执行计算 → 结果写入存储，得到 `result_ref`。
4. 消费者回调后端：POST `/api/jobs/{id}/result`，或直接更新 `/api/jobs/{id}` 的状态为 `SUCCEEDED/FAILED`。
5. 前端通过 `/api/jobs` 与 `/api/jobs/{id}` 查询任务列表与状态，并提供日志与产物下载视图（与现有路由风格一致，见[master/ARCHITECTURE.md](file:///c:/home/Projects/proteinx_infra/master/ARCHITECTURE.md#L97-L124)）。

## 5. 队列与任务定义
- 队列消息只存元数据与引用：
  - `experiment_id`：幂等键
  - `flags`：实验参数（JSON/kv）
- 结果与状态：
  - 结果落存储，队列仅传 `result_ref`。
  - 后端维护状态机：`PENDING → RUNNING → SUCCEEDED/FAILED`，记录 `attempts`、`error`、`trace` 与时间戳。
- 幂等与去重：
  - 以 `experiment_id` 作为幂等键，重复执行覆盖同一结果条目或拒绝重复。
  - 任务函数内部需保证可重入（失败重试不会产生副作用）。

## 6. 可靠性与持久化
- Redis 配置建议：
  - 开启 AOF：`appendonly yes`；建议 `appendfsync everysec`（性能与可靠性平衡）。
  - 将 `/data/redis`（或自定义）挂载为持久卷，避免容器重建数据丢失。
- RQ 行为：
  - 使用 `timeout` 与 `retries`（或在任务函数中封装重试逻辑）；失败进入 FailedJobRegistry。
  - worker 异常退出时，StartedJobRegistry 可结合超时与清理策略将“卡住”的任务重新入队（可用定时任务或 `rq-scheduler`）。
  - 单 worker 串行消费，避免预取引发的不公平与内存放大。
- 监控与告警：
  - 暴露基础日志与任务失败率、队列堆积量；可接入 `rq-dashboard`。
  - 失败超阈值入“死信列表”（DB 表或文件），管理端提示与报警。

## 7. Docker 与 Compose 集成
- 新增服务：`redis` 与 `rq-worker`（示例片段，与现有 Compose 保持同网络 `px-net`，见[docker-compose.yml](file:///c:/home/Projects/proteinx_infra/master/docker-compose.yml#L5-L42)）

```yaml
services:
  redis:
    image: redis:7-alpine
    command: ["redis-server","--appendonly","yes","--appendfsync","everysec"]
    container_name: redis
    volumes:
      - ${WORKDIR_HOST}/redis:/data
    restart: unless-stopped
    networks:
      - px-net

  rq-worker:
    build:
      context: ./queue
      dockerfile: Dockerfile
    container_name: rq-worker
    depends_on:
      - backend
      - redis
    env_file:
      - .env
    environment:
      - REDIS_URL=redis://redis:6379/0
      - QUEUE_NAME=experiments
    command: ["rq","worker","-u","${REDIS_URL}","${QUEUE_NAME}"]
    restart: unless-stopped
    networks:
      - px-net
```

- 说明：
  - `REDIS_URL` 为连接字符串；`QUEUE_NAME` 指定监听队列名称。
  - 并发设为 1 保证顺序执行；后续如需扩大并发，可启动多个 worker 或迁移到更强队列方案。

## 8. 后端集成与 API 约定
- 任务创建：
  - POST `/api/jobs`：后端写入队列并返回 `job_id`（可使用 `experiment_id` 或内部生成）。
- 任务状态与结果：
  - GET `/api/jobs`、`/api/jobs/{id}`：列表与详情（含 `status/attempts/error/result_ref`）。
  - POST `/api/jobs/{id}/cancel`：取消任务（消费者执行安全点检查并中止）。
  - POST `/api/jobs/{id}/result`（或内部服务更新）：消费者完成后更新状态与结果引用。
- 安全：
  - 与现有 JWT/PSK 机制一致，队列消费者调用后端需携带服务令牌。
  - 敏感配置通过 env_file 注入，避免入仓，参见[backend/ARCHITECTURE.md](file:///c:/home/Projects/proteinx_infra/master/backend/ARCHITECTURE.md#L87-L116)。

## 9. 运维与监控
- 日志与定位：
  - 消费者输出结构化日志（JSON 或简洁文本），包含 `job_id/experiment_id`、阶段与耗时。
  - 后端记录状态流转与错误堆栈，便于从前端监控视图检索。
- 健康检查：
  - 消费者提供简单健康判断（进程存活与队列深度）；Redis 定期备份。
- 安全与网络：
  - 保持容器仅在 `px-net` 内通信；如暴露管理界面或健康端口，限制到内网并加认证。

## 10. 迁移与扩展
- 吞吐或并发增长：
  - 启动多个 RQ worker 或迁移到 RabbitMQ + Dramatiq/Celery，获取更强的确认与编排能力。
- 工作流编排：
  - 当前以单任务为主；如需依赖/并行汇总，可在后端增加编排层或迁移到 Celery。

## 11. 风险与取舍
- 至少一次语义：可能重复执行，务必做好幂等。
- 进行中任务的崩溃恢复：通过超时与 StartedJobRegistry 清理/重入队策略处理。
- 大对象处理：队列仅传引用，结果统一落外部存储，避免 Redis 内存膨胀。

## 12. 实施清单（后续开发）
- 在 `queue` 目录新增任务模块（如 `worker_app.py`），实现任务函数供 RQ 调用。
- 后端集成 RQ 客户端，在创建 Job 的路由中入队，记录 `job_id/experiment_id` 与状态。
- 在 Compose 中新增 `redis` 与 `rq-worker` 服务，设置 `REDIS_URL` 与 `QUEUE_NAME`，并加入 `px-net`。
