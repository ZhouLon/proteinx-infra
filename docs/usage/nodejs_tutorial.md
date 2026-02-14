# Node.js 快速入门教程

## 1. 简介
Node.js 是一个基于 **Chrome V8 引擎** 的 JavaScript **运行时环境 (Runtime Environment)**。
它让 JavaScript 能够脱离浏览器，在服务器端运行。

### 核心特性
1.  **非阻塞 I/O (Non-blocking I/O)**：
    *   采用事件驱动模型，处理高并发请求时不需要为每个请求创建新线程。
    *   适合 I/O 密集型应用（如 Web 服务器、实时聊天、API 网关）。
2.  **单线程 (Single Threaded)**：
    *   主线程是单线程的，避免了多线程上下文切换的开销和复杂的锁机制。
    *   底层使用 `libuv` 处理异步任务（文件读写、网络请求等），实现并发。
3.  **跨平台**：
    *   一份代码可以在 Windows, macOS, Linux 上运行。
4.  **庞大的生态系统 (NPM)**：
    *   拥有世界上最大的开源库生态系统，几乎任何功能都能找到现成的包。

### Node.js 能做什么？
1.  **Web 后端服务** (API Server, SSR)
    *   如 Express, Koa, NestJS 框架构建 RESTful/GraphQL API。
2.  **实时应用** (Real-time Applications)
    *   如 WebSocket 聊天室、在线协作工具、游戏服务器。
3.  **构建工具与自动化脚本** (Build Tools & CLI)
    *   前端构建 (Webpack, Vite), 自动化测试, 文件处理脚本。
4.  **桌面应用** (Desktop Apps)
    *   基于 Electron 开发跨平台桌面软件 (如 VS Code, Slack)。
5.  **物联网 (IoT)**
    *   轻量级，适合在树莓派等嵌入式设备上运行。

### 不适合做什么？
*   **CPU 密集型任务** (如视频编码、复杂数学运算)：
    *   因为是单线程，长时间的 CPU 占用会阻塞主线程，导致无法处理其他请求。
    *   *解决方案*：使用 Worker Threads 或将计算任务交给 C++/Rust 扩展。

## 2. 安装
- **Windows**: 访问 [Node.js 官网](https://nodejs.org/) 下载 LTS 版本安装包并运行。
- **macOS**: 使用 Homebrew 安装: `brew install node`
- **Linux**: 使用包管理器 (如 `apt install nodejs npm`) 或 nvm 安装。

## 3. Hello World
创建一个名为 `hello.js` 的文件：

```javascript
console.log('Hello, Node.js!');
```

运行：
```bash
node hello.js
```

## 4. 创建简单的 HTTP 服务器
创建一个名为 `server.js` 的文件：

```javascript
const http = require('http');

const hostname = '127.0.0.1';
const port = 3000;

const server = http.createServer((req, res) => {
  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/plain');
  res.end('Hello World\n');
});

server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});
```

运行服务器：
```bash
node server.js
```
访问 `http://127.0.0.1:3000` 查看结果。

## 5. NPM (Node Package Manager)
NPM 是 Node.js 的包管理器。

- **初始化项目**: `npm init -y` (生成 package.json)
- **安装依赖**: `npm install express`
- **安装开发依赖**: `npm install nodemon --save-dev`

## 6. 使用 Express 框架 (更简单的 Web 服务器)
首先安装 Express: `npm install express`

创建 `app.js`:

```javascript
const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
  res.send('Hello from Express!');
});

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`);
});
```

## 7. 异步编程
Node.js 核心是异步的。

### 回调函数 (Callback)
```javascript
const fs = require('fs');
fs.readFile('hello.js', 'utf8', (err, data) => {
  if (err) throw err;
  console.log(data);
});
```

### Promise & Async/Await (推荐)
```javascript
const fs = require('fs').promises;

async function readFile() {
  try {
    const data = await fs.readFile('hello.js', 'utf8');
    console.log(data);
  } catch (err) {
    console.error(err);
  }
}

readFile();
```

## 8. 常用内置模块
- `fs`: 文件系统操作
- `path`: 路径处理
- `http`: 创建 HTTP 服务器
- `os`: 操作系统信息
- `events`: 事件触发器

## 9. 调试
- 使用 `console.log`
- 使用 VS Code 内置调试器 (F5)
- 使用 `node --inspect index.js`

## 10. 下一步
- 学习 Express/Koa/NestJS 框架
- 学习数据库连接 (MongoDB/MySQL)
- 学习 RESTful API 设计
