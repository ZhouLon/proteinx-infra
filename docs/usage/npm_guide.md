# NPM 使用指南：Node.js 的瑞士军刀

## 1. 什么是 NPM？
**NPM (Node Package Manager)** 是世界上最大的软件注册表，也是 Node.js 默认的包管理工具。
*   **作用**：帮你安装别人写好的代码（包/依赖），比如 `React`, `Vue`, `Express`。
*   **地位**：相当于 Python 的 `pip`，Java 的 `Maven`，Linux 的 `apt/yum`。

## 2. 核心文件：package.json
每个 Node.js 项目根目录下都有一个 `package.json`，它是项目的“身份证”和“说明书”。

```json
{
  "name": "my-project",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",        // 开发命令
    "build": "vite build" // 构建命令
  },
  "dependencies": {       // 生产环境依赖 (运行时需要)
    "react": "^18.2.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {    // 开发环境依赖 (只在开发/构建时需要)
    "typescript": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

## 3. 常用命令速查

### 初始化项目
```bash
# 交互式创建 package.json (问你一堆问题)
npm init

# 快速创建 (全部使用默认值)
npm init -y
```

### 安装依赖 (Install)
```bash
# 安装 package.json 中列出的所有依赖 (最常用)
# 场景：刚拉取别人的代码，或者 Docker 构建时
npm install
# 简写
npm i

# 安装指定包 (并写入 dependencies)
# 场景：项目需要用到 axios 发请求
npm install axios

# 安装指定包到开发依赖 (写入 devDependencies)
# 场景：安装 TypeScript, ESLint 等工具
npm install typescript --save-dev
# 简写
npm i -D typescript

# 全局安装 (安装到系统目录，不推荐，除非是 CLI 工具)
npm install -g create-react-app
```

### 运行脚本 (Scripts)
对应 `package.json` 中 `scripts` 字段定义的命令。
```bash
# 启动开发服务器
npm run dev

# 构建生产包
npm run build

# 运行测试
npm run test

# 特例：start 命令可以省略 run
npm start
```

### 管理包
```bash
# 卸载包
npm uninstall axios

# 更新包 (根据 package.json 允许的版本范围)
npm update

# 查看当前安装的包列表
npm list
```

## 4. package-lock.json 是什么？
*   **现象**：当你执行 `npm install` 后，会自动生成一个 `package-lock.json` 文件。
*   **作用**：**锁定依赖版本**。
    *   `package.json` 里写的通常是模糊版本 (如 `^1.8.0`，表示允许安装 `1.8.x` 或 `1.9.x`)。
    *   `package-lock.json` 里写的是**精确版本** (如 `1.8.2`) 以及它的下载地址、哈希值。
*   **目的**：确保你的同事、CI/CD 服务器、Docker 容器安装的依赖版本**完全一致**，避免“我这里能跑，你那里报错”的玄学问题。
*   **注意**：**必须提交到 Git**！不要忽略它。

## 5. 常见问题
*   **Q: npm 安装太慢怎么办？**
    *   A: 切换到国内镜像源（淘宝源）。
    ```bash
    npm config set registry https://registry.npmmirror.com
    ```
*   **Q: `node_modules` 文件夹太大了能删吗？**
    *   A: 可以。只要有 `package.json`，随时可以用 `npm install` 重新生成它。**绝对不要提交 `node_modules` 到 Git**。
*   **Q: `dependencies` 和 `devDependencies` 放错了会怎样？**
    *   A: 对前端项目（Webpack/Vite 打包）来说，**几乎没影响**，因为打包工具会把所有用到的代码都打进去。但为了规范，还是建议区分清楚（工具类放 dev，框架类放 dep）。
