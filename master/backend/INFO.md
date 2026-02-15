# 后端重构说明

## 目标
- 路由处理模块与业务逻辑分离
- 数据访问与工具函数集中管理
- 保持现有 API 路径与行为不变
- 如果对路由函数修改后，也需要修改 INFO.md 中的路由说明

## 新目录结构
```
backend/
├── main.py
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models/
│   │   └── __init__.py
│   ├── utils/
│   │   ├── common.py
│   │   ├── db.py
│   │   ├── path.py
│   │   └── security.py
│   ├── services/
│   │   └── project_service.py
│   └── routes/
│       ├── auth.py
│       ├── projects.py
│       ├── metadata.py
│       ├── recycle.py
│       └── files_jobs_overview.py
```

## 模块依赖关系图
```
main.py
 ├─ app.routes.auth ─┐
 ├─ app.routes.projects ─┬─ app.services.project_service ─┬─ app.utils.db
 ├─ app.routes.metadata  ─┘                             ├─ app.utils.common
 ├─ app.routes.recycle   ───────────────────────────────┴─ app.utils.security
 └─ app.routes.files_jobs_overview ── app.utils.path
                                  └─ app.config
app.models 被上述所有模块引用
```

## 使用示例（导入路径）
```python
from app.services.project_service import read_project_info, write_project_info
from app.utils.db import get_db_conn, resolve_table
from app.utils.security import hash_password
from app.utils.common import normalize_name
from app.routes.projects import router as projects_router
```



## 路由与功能清单

- 认证（app/routes/auth.py）
  - GET /api/auth/exists：检查是否已注册用户
  - POST /api/auth/register：注册用户并持久化用户名与密码哈希
  - POST /api/auth/token：校验用户名与密码，返回访问令牌信息（mock）
  - GET /api/auth/me：返回当前已注册用户信息
  - POST /api/auth/refresh：刷新令牌（mock）

- 文件与作业、概览（app/routes/files_jobs_overview.py）
  - GET /api/nodes：返回节点列表（mock）
  - GET /api/nodes/{node_id}：返回节点详情（mock）
  - POST /api/jobs：创建作业（mock）
  - GET /api/jobs：作业列表（mock）
  - GET /api/jobs/{job_id}：作业详情（mock）
  - GET /api/jobs/{job_id}/logs：作业日志（mock）
  - POST /api/jobs/{job_id}/cancel：取消作业（mock）
  - GET /api/files/list：列出指定目录下文件与文件夹（根目录自动创建）
  - POST /api/files/upload：上传文件到指定目录
  - DELETE /api/files：删除指定路径（文件或目录）
  - GET /api/files/preview：预览文本文件前 4KB
  - GET /api/overview：聚合节点、作业与文件统计（递归遍历 WORKDIR）

- 元数据（SQLite）（app/routes/metadata.py）
  - GET /api/metadata/tables：列出库内非系统表
  - GET /api/metadata/columns：列出指定表的列信息
  - GET /api/metadata/query：支持分页与筛选（构造 WHERE，参数化查询）

- 项目与数据集（app/routes/projects.py）
  - GET /api/projects：项目列表（置顶优先、再按创建时间降序）
  - POST /api/projects：创建项目（名称规范化、重复名校验）
  - GET /api/projects/{pid}：项目详情
  - PATCH /api/projects/{pid}：更新项目名称/描述（更新时间）
  - POST /api/projects/{pid}/pin：置顶项目（记录置顶时间）
  - POST /api/projects/{pid}/unpin：取消置顶
  - DELETE /api/projects/{pid}：验证密码后移动至回收站并写入删除元数据
  - POST /api/projects/{pid}/datasets：基于筛选条件创建数据集并计算行数
  - GET /api/projects/{pid}/datasets：分页列出项目数据集定义

- 回收站（app/routes/recycle.py）
  - GET /api/recycle/projects：回收项目列表（含 30 天自动清理逻辑）
  - POST /api/recycle/projects/{pid}/restore：检查名称冲突后从回收站还原
  - DELETE /api/recycle/projects/{pid}：永久删除回收站条目

