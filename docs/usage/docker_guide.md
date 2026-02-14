# Docker 极简实战指南

## 1. 什么是 Docker？
Docker 是一个开源的**应用容器引擎**。
简单比喻：
*   **物理机/虚拟机**：像是一栋独立的别墅（可以在里面装任何家具，但搬家很麻烦，要连地基一起搬）。
*   **Docker 容器**：像是标准化的集装箱。
    *   **标准化**：无论你的集装箱里装的是大米（Python）还是汽车（Node.js），外表尺寸都一样，码头吊车（服务器）不需要知道里面是什么就能搬运。
    *   **隔离性**：集装箱A里的货物不会弄脏集装箱B。
    *   **轻量级**：不需要建地基，直接放在船甲板（宿主机内核）上。

**核心概念三剑客**：
1.  **镜像 (Image)**：软件的安装包（只读）。比如 Windows 安装光盘。
2.  **容器 (Container)**：镜像运行起来的实例（可读写）。比如安装好并正在运行的 Windows 系统。
3.  **仓库 (Registry)**：存放镜像的云端超市。比如 Docker Hub。

## 2. 为什么要用 Docker？
在 ProteinX Infra 项目中，Docker 解决了著名的“**在我的机器上能跑**”问题。
*   前端用 Node 18，后端用 Python 3.11，数据库用 PostgreSQL 15。
*   如果没有 Docker，你需要在一个新服务器上手动安装这三个软件，还要配置环境变量、解决版本冲突。
*   有了 Docker，你只需要一句命令 `docker-compose up`，三个服务就全部以标准容器启动了。

## 3. 常用命令速查

### 镜像操作 (Image)
```bash
# 从仓库拉取镜像
docker pull python:3.11-slim

# 查看本地镜像
docker images

# 删除镜像
docker rmi <image_id>

# 构建镜像 (读取当前目录 Dockerfile)
docker build -t my-app:v1 .
```

### 容器操作 (Container)
```bash
# 启动容器
# -d: 后台运行 (Detached)
# -p: 端口映射 (宿主机端口:容器端口)
# --name: 给容器起个名字
docker run -d -p 8080:80 --name my-web-server nginx

# 查看正在运行的容器
docker ps

# 查看所有容器 (包括已停止的)
docker ps -a

# 停止容器
docker stop my-web-server

# 删除容器 (必须先停止)
docker rm my-web-server

# 查看容器日志 (排错神器)
docker logs -f my-web-server

# 进入容器内部 (像 SSH 一样)
docker exec -it my-web-server /bin/bash
# (如果是 alpine 基础镜像，通常用 /bin/sh)
```

## 4. Dockerfile 编写指南
Dockerfile 是制作镜像的“菜谱”。

**示例：前端项目的菜谱**
```dockerfile
# 1. 选材：基于 Node.js 18 的轻量版系统
FROM node:18-alpine

# 2. 备菜台：设置工作目录
WORKDIR /app

# 3. 预处理：先把依赖清单拷进去
COPY package.json ./

# 4. 腌制：安装依赖 (这一步最耗时，利用缓存)
RUN npm install

# 5. 下锅：把剩下的代码都拷进去
COPY . .

# 6. 烹饪：打包构建
RUN npm run build

# 7. 装盘：暴露 3000 端口
EXPOSE 3000

# 8. 上菜：启动命令
CMD ["npm", "run", "preview"]
```

## 5. Docker Compose (大杀器)
一个项目通常有多个服务（前端、后端、数据库）。一个个 `docker run` 太累了。
Docker Compose 允许你用一个 `docker-compose.yml` 文件定义一组服务，一键启动。

**示例：同时启动 Web 和 Redis**
```yaml
version: '3'
services:
  web:
    build: ./frontend
    ports:
      - "80:80"
  redis:
    image: "redis:alpine"
    ports:
      - "6379:6379"
```

**命令**：
*   启动所有服务：`docker-compose up -d`
*   停止所有服务：`docker-compose down`

## 6. 常见问题 Q&A
*   **Q: 容器里的数据重启会丢吗？**
    *   A: 会！容器是临时的。如果你要保存数据库文件，必须挂载**卷 (Volume)**。
    *   `docker run -v /host/data:/container/data ...`
*   **Q: `127.0.0.1` 在容器里是什么？**
    *   A: 是容器自己！如果你在容器里访问宿主机的数据库，不能用 `localhost`，要用 `host.docker.internal` (Mac/Win) 或宿主机真实 IP。
