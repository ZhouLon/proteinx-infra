# 第一阶段：构建 (Build Stage)
FROM node:18-alpine AS builder

WORKDIR /app

# 先拷贝 package.json 和 lock 文件，利用 Docker 缓存加速
COPY package.json package-lock.json* ./

# 安装依赖
RUN npm install

# 拷贝源代码
COPY . .

# 构建生产环境代码 (生成 dist 目录)
RUN npm run build

# 第二阶段：运行 (Run Stage)
FROM nginx:alpine

# 拷贝构建产物到 Nginx 目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 拷贝自定义 Nginx 配置文件 (解决 React Router 刷新 404 问题)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
