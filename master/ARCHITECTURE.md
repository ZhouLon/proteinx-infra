# ProteinX Infra Master 前端架构文档

## 1. 概览
本项目 (`master`) 是 ProteinX Infra 的管理控制台（Master 管理端），基于 **React 18** + **TypeScript** + **Vite** 构建。它采用**单页应用 (SPA)** 架构，通过 API 与后端交互。

Master 管理端面向分布式的 **Master-Worker** 部署形态：
- 前端与后端拆分为两个容器：前端容器仅负责静态资源与反代，后端容器提供 API
- 前端容器使用 Nginx 服务静态页面，并将 `/api/*` 反向代理到后端容器（如 `backend:8000`，通过同一 Docker 网络解析）
- 计算端 Worker 通过心跳与任务队列接入，执行训练并回传产物

## 2. 核心技术栈
*   **框架**: React 18 (Hooks, 函数式组件)
*   **语言**: TypeScript (强类型，减少运行时错误)
*   **构建工具**: Vite (极速开发体验，Rollup 打包)
*   **UI 组件库**: Ant Design 5 (企业级后台组件)
*   **路由**: React Router v6 (声明式路由)
*   **网络请求**: Axios (拦截器封装)
*   **图标库**: @ant-design/icons

## 3. 目录结构
```text
master/
├── frontend/                 # 前端工程（React + Vite）
│   ├── src/                  # 页面、组件、API 封装
│   ├── index.html
│   ├── package.json
│   ├── tsconfig*.json
│   ├── vite.config.ts
│   └── Dockerfile            # 前端镜像（Nginx 运行静态资源 + 反代 /api 到 backend）
├── backend/                  # 后端工程（FastAPI）
│   ├── app/                  # 应用代码（路由、模型）
│   │   └── main.py
│   ├── requirements.txt      # 后端依赖
│   ├── nginx.conf            # 前端容器内 Nginx 配置（反代到 backend:8000）
│   └── Dockerfile            # 后端镜像（uvicorn 运行）
└── ARCHITECTURE.md
```

## 4. 关键设计决策

### 4.1 资源管理策略
*   **移除了 `public` 目录**：
    *   所有静态资源（图片、Logo、Favicon）统一放入 `src/assets`。
    *   **优势**：这些资源会被 Vite 处理（Hash 命名、压缩、Base64 内联），避免缓存问题，且能在代码中通过 `import` 引用，享受 TypeScript 类型检查。

### 4.2 路由策略 (App.tsx)
系统直接进入登录页与控制台；初始化工作目录在容器启动前由运维预先设定（通过 Compose 卷挂载），前端不再承担初始化流程。

### 4.3 样式方案
*   主要使用 Ant Design 的组件样式。
*   自定义样式推荐使用 CSS Modules 或内联 `style` (简单场景)。
*   全局重置样式在 `main.tsx` 中引入 `antd/dist/reset.css`。

### 4.4 API 交互
*   所有 HTTP 请求必须通过 `src/api` 目录下的函数发起，**禁止在组件中直接写 `axios.get`**。
*   这样做的目的是为了统一管理接口路径、参数类型和响应结构。

### 4.5 安全与认证
*   用户会话使用 JWT（Access + Refresh），前端持有短期令牌并自动刷新
*   Worker 节点接入需提供 Token 或预共享密钥（PSK）
*   通过后端环境变量配置敏感信息（Redis、MinIO、数据库），前端仅经由 `/api` 访问后端

### 4.6 持久化与 WorkDir
*   宿主机工作目录在部署前人为确定，并通过 Compose `volumes` 映射到后端容器内路径 `/data`
*   业务访问的容器数据根为 `/data`，其内容全部映射并落在宿主机工作目录
*   前端仅负责配置与展示，不直接读写非挂载路径

### 4.7 节点与任务视图
*   页面提供“节点池”视图展示 Worker 状态（在线、空闲、忙碌）
*   任务列表展示训练作业状态（pending、running、finished、failed）
*   日志与指标面板通过 WebSocket/轮询实时更新

### 4.8 文件存储与队列
*   文件存储由后端对接 MinIO 或本地文件系统
*   队列与调度由后端对接 Redis（Celery/RQ），前端使用 API 触发与查询

## 5. 页面模块
*   数据中心：统一上传元数据、数据预览与校验
*   项目列表与详情：子模型配置、参数管理与画布
*   训练配置与执行：AMP/DDP、评估轮次、启动训练
*   训练监控：实时损失曲线与 GPU 利用率
*   产物归档与对比：模型权重、评估报告、历史实验对比

## 6. API 接口清单
基础路径：`/api`（前端容器 Nginx 反代到后端容器 `backend:8000`）

### 系统
（初始化由部署阶段完成，无对应 API）

### 认证
- POST `/auth/token`：登录获取 Access/Refresh Token
- GET `/auth/me`：获取当前用户信息
- POST `/auth/refresh`：刷新 Access Token

### 节点
- GET `/nodes`：获取节点列表（CPU/GPU/心跳等）
- GET `/nodes/{id}`：获取节点详情
- DELETE `/nodes/{id}`：删除/注销节点

### 任务
- POST `/jobs`：创建训练任务
- GET `/jobs`：任务列表
- GET `/jobs/{id}`：任务详情
- GET `/jobs/{id}/logs`：任务日志
- POST `/jobs/{id}/cancel`：取消任务
- GET `/jobs/{id}/artifacts/download`：下载产物（前端约定路径，后端待实现）

### 文件
- GET `/files/list?path=`：列出 WorkDir 文件/目录
- POST `/files/upload`：上传文件（multipart/form-data）
- DELETE `/files?path=`：删除文件
- GET `/files/preview?path=`：文件预览内容

## 7. 开发指南
*   **启动开发服务器**: `npm run dev`
*   **构建生产代码**: `npm run build`
*   **类型检查**: `tsc`

## 8. 部署
**前后端拆分（推荐）**
```
# 1) 先在 .env 设置宿主机与容器内工作目录
# WORKDIR_HOST=C:/ProteinXWorkdir
# WORKDIR_CONTAINER=/data

# 2) 使用 Compose 启动（本地已构建镜像或拉取镜像）
docker compose up -d
```

**Nginx 反代说明**
```
# 见 master/nginx.conf：
# location /api/ {
#   proxy_pass http://backend:8000/;
# }
```
