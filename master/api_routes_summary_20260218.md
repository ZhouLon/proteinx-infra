# API 与路由汇总（Master）

- 说明：前后端交互的 API 按路由文件划分，列出路径与对应的前端模块。

## 认证（auth）
- 后端：backend/app/routes/auth.py
- 前端：frontend/src/api/auth.ts
- 路径：
  - GET /api/auth/exists
  - POST /api/auth/register
  - POST /api/auth/token
  - GET /api/auth/me
  - POST /api/auth/refresh

## 元数据（metadata）
- 后端：backend/app/routes/metadata.py
- 前端：frontend/src/api/metadata.ts
- 路径：
  - GET /api/metadata/tables
  - GET /api/metadata/columns
  - GET /api/metadata/query

## 项目（projects）
- 后端：backend/app/routes/projects.py
- 前端：frontend/src/api/projects.ts
- 路径：
  - GET /api/projects
  - POST /api/projects
  - GET /api/projects/{pid}
  - PATCH /api/projects/{pid}
  - POST /api/projects/{pid}/pin
  - POST /api/projects/{pid}/unpin
  - DELETE /api/projects/{pid}
  - POST /api/projects/{pid}/datasets
  - GET /api/projects/{pid}/datasets

## 回收站（recycle）
- 后端：backend/app/routes/recycle.py
- 前端：frontend/src/api/recycle.ts
- 路径：
  - GET /api/recycle/projects
  - POST /api/recycle/projects/{pid}/restore
  - DELETE /api/recycle/projects/{pid}

## 文件（files）
- 后端：backend/app/routes/files.py
- 前端：frontend/src/api/files.ts
- 路径：
  - GET /api/files/list
  - POST /api/files/upload
  - DELETE /api/files
  - GET /api/files/preview

## 作业与节点与概览（jobs_nodes_overview）
- 后端：backend/app/routes/jobs_nodes_overview.py
- 前端：frontend/src/api/jobs_nodes_overview.ts
- 路径：
  - GET /api/nodes
  - GET /api/nodes/{node_id}
  - POST /api/jobs
  - GET /api/jobs
  - GET /api/jobs/{job_id}
  - GET /api/jobs/{job_id}/logs
  - POST /api/jobs/{job_id}/cancel
  - GET /api/overview
