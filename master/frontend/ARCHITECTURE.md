# ProteinX Infra Master 前端架构

## 1. 概览
- 技术栈：React 18、TypeScript、Vite、Ant Design、React Router、Axios
- 目标：提供主控节点的可视化管理与操作界面，支持认证、项目/数据集管理、监控与文档查看
- 入口：[main.tsx](file:///c:/home/Projects/proteinx_infra/master/frontend/src/main.tsx)、[App.tsx](file:///c:/home/Projects/proteinx_infra/master/frontend/src/App.tsx)

## 2. 目录结构
```
frontend/
├── ARCHITECTURE.md           # 本文档
├── src/
│   ├── api/                  # API 封装
│   │   ├── client.ts         # Axios 实例与拦截器
│   │   ├── auth.ts           # 认证相关请求
│   │   ├── metadata.ts       # 元数据相关请求
│   │   ├── file.ts           # 文件相关请求
│   │   ├── job.ts            # 作业相关请求
│   │   └── node.ts           # 节点相关请求
│   ├── layouts/
│   │   └── MainLayout.tsx    # 主布局（Sider/Header/Content/Footer）
│   ├── pages/                # 页面路由
│   │   ├── Login/            # 登录
│   │   ├── Register/         # 注册
│   │   ├── DashboardHome/    # 仪表盘首页
│   │   ├── ProjectList/      # 项目列表
│   │   ├── ProjectDetail/    # 项目详情（子路由：overview/data-build/datasets/...）
│   │   ├── DataManagement/   # 数据管理
│   │   ├── TrainingMonitor/  # 训练监控
│   │   ├── Docs/             # 文档查看
│   │   ├── Recycle/          # 回收站
│   │   ├── User/             # 用户页（退出登录）
│   │   └── Visualization/    # 可视化占位
│   ├── App.tsx               # 路由配置与认证跳转
│   ├── main.tsx              # 渲染入口
│   └── vite-env.d.ts         # 类型声明
├── index.html                # Vite HTML 入口
├── vite.config.ts            # Vite 配置
├── package.json              # 依赖与脚本
├── tsconfig.json             # TS 配置
├── tsconfig.node.json        # Node 构建 TS 配置
├── Dockerfile                # 前端容器镜像
└── nginx.conf                # 部署时的 Nginx 反代配置
```

## 3. 路由与页面
- 路由框架：React Router v6
- 顶级路由：
  - `/`：根据是否存在用户与是否已认证，重定向到 `/dashboard` 或 `/login` 或 `/register`（首次启动）
  - `/login`、`/register`：认证入口
  - `/dashboard`：带主布局的受保护区域（需要认证）
- 子路由：
  - `/dashboard` 下挂载各业务页面，如项目列表、项目详情子路由、数据管理、监控、文档、回收站、用户页
- 主要文件：
  - 路由与守卫逻辑：[App.tsx](file:///c:/home/Projects/proteinx_infra/master/frontend/src/App.tsx)
  - 主布局与导航：[MainLayout.tsx](file:///c:/home/Projects/proteinx_infra/master/frontend/src/layouts/MainLayout.tsx)

## 4. 认证与安全
- 令牌管理：
  - 登录成功后保存 `access_token` 与 `refresh_token` 至 `sessionStorage`
  - 登录成功触发 `window.dispatchEvent(new Event('px-auth'))`，用于全局状态更新
- Axios 拦截与自动刷新：
  - 请求拦截器在存在 `access_token` 时注入 `Authorization: Bearer`
  - 响应拦截器在收到 401 时尝试使用 `refresh_token` 交换新的 `access_token`；失败则清除令牌并重定向至 `/login`
  - 实现位置：[client.ts](file:///c:/home/Projects/proteinx_infra/master/frontend/src/api/client.ts)
- 路由守卫：
  - `App.tsx` 在首次加载时通过 `/api/auth/exists` 判断是否存在已注册用户
  - 根据 `sessionStorage` 的令牌存在与否决定重定向目标（`/dashboard` 或 `/login`）；受保护区域使用 `<Navigate>` 强制跳转
- 退出登录：
  - 用户页提供“退出登录”按钮，清除令牌并跳回 `/login`：[pages/User/index.tsx](file:///c:/home/Projects/proteinx_infra/master/frontend/src/pages/User/index.tsx)
- 混淆策略（后端配合）：
  - 被封禁 IP 的所有请求返回 404；密码错误返回 401
  - 前端提示统一为通用错误文案，避免泄露细节

## 5. 布局与 UI
- UI 库：Ant Design v5
- 主布局：
  - Sider：菜单与用户头像/名称区域（点击进入用户页）
  - Header：标题与全局样式
  - Content：承载具体页面内容（`<Outlet />`）
  - Footer：版权信息
- 响应式与样式：
  - 以 AntD 主题为基础，辅以简单内联样式，满足快速迭代与可维护性

## 6. API 层
- Axios 实例：[api/client.ts](file:///c:/home/Projects/proteinx_infra/master/frontend/src/api/client.ts)
- 业务 API：
  - 认证：[api/auth.ts](file:///c:/home/Projects/proteinx_infra/master/frontend/src/api/auth.ts)
  - 元数据：[api/metadata.ts](file:///c:/home/Projects/proteinx_infra/master/frontend/src/api/metadata.ts)
  - 文件与作业：[api/file.ts](file:///c:/home/Projects/proteinx_infra/master/frontend/src/api/file.ts)、[api/job.ts](file:///c:/home/Projects/proteinx_infra/master/frontend/src/api/job.ts)
  - 节点：[api/node.ts](file:///c:/home/Projects/proteinx_infra/master/frontend/src/api/node.ts)
- 约定：
  - `baseURL` 为 `/api`，通过 Nginx 将前端的 `/api` 反代到后端容器

## 7. 状态管理
- 轻量模式：
  - 使用 React 组件本地状态与 `sessionStorage` 作为令牌持久化
  - 通过浏览器事件 `px-auth` 通知应用刷新认证状态
- 如需全局复杂状态可演进至 Redux 或 Zustand；当前场景暂不需要

## 8. 构建与部署
- 脚本：
  - `npm run dev`：本地开发
  - `npm run build`：类型检查并构建
  - `npm run preview`：预览构建结果
- 部署：
  - 生产环境由 Nginx 提供静态资源，并反代 `/api` 到后端容器（参考 [nginx.conf](file:///c:/home/Projects/proteinx_infra/master/frontend/nginx.conf)）
  - 后端容器不对宿主机暴露端口，仅通过容器网络被前端访问

## 9. 配置与环境
- 前端通常不需要额外 .env；如需自定义 API 入口，可引入 `VITE_API_BASE` 并在 `client.ts` 使用
- 认证令牌存储在 `sessionStorage`，刷新逻辑由拦截器自动处理

## 10. 扩展点
- 统一错误处理：在 Axios 层集中处理业务错误并给出一致提示
- 权限控制：根据用户角色动态调整菜单与页面访问
- 国际化：接入 i18n 以支持中英文切换
- 性能优化：按需加载路由与组件、图片懒加载、资源压缩与缓存策略
