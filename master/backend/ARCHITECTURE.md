# ProteinX Infra Master 后端架构

## 1. 概览
- 技术栈：FastAPI（Python 3.11）、Pydantic、SQLite、Uvicorn
- 目标：提供项目与数据集管理、元数据查询、文件/作业管理、认证与安全防护
- 入口：[main.py](/proteinx_infra/master/backend/app/main.py)

## 2. 目录结构
```
backend/
├── ARCHITECTURE.md           # 本文档
├── INFO.md                   # 路由说明（维护约定）
├── app/
│   ├── config.py             # 环境变量与路径配置、日志与安全参数
│   ├── main.py               # FastAPI 入口、中间件注册与路由挂载
│   ├── models/               # Pydantic 数据模型
│   │   └── __init__.py
│   ├── utils/                # 工具模块（安全、路径、数据库、通用）
│   │   ├── security.py
│   │   ├── path.py
│   │   ├── db.py
│   │   └── common.py
│   ├── services/             # 业务逻辑（项目/数据集等）
│   │   └── project_service.py
│   └── routes/               # 路由层（HTTP API）
│       ├── auth.py
│       ├── projects.py
│       ├── metadata.py
│       ├── recycle.py
│       └── files_jobs_overview.py
```

## 3. 模块职责
- config.py
  - 工作目录 WORKDIR（容器内路径）与基础路径定义
  - 数据库、JWT、登录封禁阈值与日志/状态文件等环境变量读取
  - 日志初始化（写入 /data/logs/backend.log），确保 /data/logs 与 /data/security 目录存在
- main.py
  - 创建 FastAPI 应用，设置 CORS
  - 注册 IP 封禁中间件（命中黑名单返回 404）
  - 挂载各路由模块
- models/__init__.py
  - 统一声明 Pydantic 模型：认证参数、项目/数据集实体、文件/作业/概览结构等
  - 被各路由引用用于请求校验与响应序列化
- utils/security.py
  - 密码哈希（SHA256 + salt）
  - 轻量 JWT（HS256）编码/解码，access/refresh 令牌签发
  - BanManager：登录失败滑窗计数、封禁、持久化与审计
    - 状态文件：/data/security/auth_ban_state.json（重启后加载封禁）
    - 审计日志：/data/logs/auth_ban.log（封禁事件记录）
- utils/db.py
  - SQLite 连接管理与元数据库初始化
  - where 子句构造（列、操作符和值校验），可选 SQLCipher PRAGMA（取决于环境）
  - 表解析（针对 mutations/sources 关联查询等逻辑）
- utils/path.py
  - 受控路径映射：将用户传入路径映射到 WORKDIR，防止目录穿越
- utils/common.py
  - 通用工具：名称归一化等
- services/project_service.py
  - 项目与数据集的核心业务流程
  - 读写项目信息、数据集保存、回收站管理（软删除/还原/清理）
- routes/*
  - auth.py：注册、登录、刷新、获取当前用户；集成封禁检查与失败计数
  - projects.py：项目 CRUD、数据集创建与列表
  - metadata.py：元数据分页查询、表列表、过滤条件处理
  - recycle.py：回收站列表、还原与清理
  - files_jobs_overview.py：文件列表/上传/删除/预览；作业与概览的示例接口

## 4. 请求流与安全
- 认证
  - 登录：POST /api/auth/token（用户名/密码校验；签发 access/refresh）
  - 刷新：POST /api/auth/refresh（JSON：{ refresh_token }；签发新的 access）
  - 当前用户：GET /api/auth/me（Authorization: Bearer access_token）
- 封禁与混淆
  - 登录失败滑窗计数达到阈值则封禁 IP（默认 30 分钟）
  - 封禁期间所有路由返回 404（中间件与登录入口双重检查）
  - 封禁状态持久化，容器重建后继续生效
- CORS
  - 默认允许所有来源，生产需收紧为明确的前端域名列表
- 存储
  - 工作目录 /data 挂载于宿主机，用于日志、数据库、状态文件等
  - 建议数据库迁移到 Postgres 并启用账号权限；SQLite 适用于单实例轻量场景

## 5. 配置与环境变量
- 工作目录与数据库
  - WORKDIR_CONTAINER=/data
  - METADATA_DB=/data/metadata/database.db
- JWT
  - JWT_SECRET（强随机密钥）
  - ACCESS_TOKEN_EXPIRE_MINUTES（默认 20）
  - REFRESH_TOKEN_EXPIRE_DAYS（默认 7）
- 登录封禁
  - AUTH_FAIL_THRESHOLD（默认 5）
  - AUTH_FAIL_WINDOW_MINUTES（默认 10）
  - AUTH_BAN_MINUTES（默认 30）
  - AUTH_BAN_LOG=/data/logs/auth_ban.log
  - AUTH_BAN_STATE=/data/security/auth_ban_state.json
- 可选：DB_PASSWORD_FILE、SQLCIPHER_ENABLED（如需 SQLCipher）

## 6. 中间件与启动顺序
1. 加载配置，创建日志与安全目录
2. 初始化 FastAPI 与 CORS
3. 注册 IPBanMiddleware（封禁拦截）
4. 挂载 auth/projects/metadata/recycle/files_jobs_overview 路由
5. 启动服务（Uvicorn）

## 7. 扩展点
- 鉴权中间件：统一为非 /auth 路由加 JWT 校验依赖
- 速率限制：为登录与高频接口在网关层接入限流（Nginx/WAF）或后端中间件
- 存储迁移：SQLite → Postgres（账号认证、角色权限），配合 ORM（SQLAlchemy）
- 日志策略：滚动与结构化日志（JSON），接入集中式日志（ELK）
- 安全头：HSTS、CSP、X-Frame-Options 等

## 8. 部署建议
- 前端容器对外开放 80/443，反代 /api 到后端容器内网地址
- 后端容器不暴露宿主机端口，仅容器网络可见
- 所有敏感配置通过 env_file/secrets 注入，严禁入仓
- 使用 HTTPS 与严格 CORS；开启基础 WAF 规则与限流
