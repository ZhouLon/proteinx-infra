# React 实战指南：从零理解与使用

## 1. 什么是 React？
React 是一个**用于构建用户界面 (User Interface)** 的 JavaScript 库，由 Facebook (Meta) 开发。

简单比喻：
*   **以前的网页开发**：像是在画板上画画。如果你想修改画面的一角，必须擦掉重画（直接操作 DOM，`document.getElementById('app').innerHTML = '...'`）。很繁琐，容易出错。
*   **React 开发**：像是在搭积木。你定义好每一个积木（组件），然后告诉 React：“把这块红积木换成蓝积木”。React 会自动帮你更新画面，而且只更新变动的那一小块（虚拟 DOM）。

## 2. React 的核心作用
1.  **组件化 (Component-Based)**：
    *   把复杂的页面拆分成独立的、可复用的“小零件”（如按钮、导航栏、表单）。
    *   好处：写一次，到处用；坏了一个修一个，不影响整体。
2.  **声明式编程 (Declarative)**：
    *   你只需要告诉 React **“界面应该长什么样”**（基于当前的数据状态）。
    *   不需要告诉它 **“怎么一步步去改”**（不用手动增删 DOM 节点）。
    *   React 会自动处理数据变化后的界面刷新。
3.  **单向数据流 (One-Way Data Flow)**：
    *   数据像瀑布一样，从父组件流向子组件（Props）。
    *   子组件不能直接修改父组件的数据，保证了数据流向清晰，易于调试。

## 3. 如何使用 React？(核心三板斧)

### 第一板斧：JSX (JavaScript XML)
在 JS 代码里直接写 HTML 标签。这是 React 的标志性语法。

```jsx
// 以前的 JS 写法 (太麻烦)
// const element = React.createElement('h1', {className: 'greeting'}, 'Hello, world!');

// React JSX 写法 (直观)
const element = <h1 className="greeting">Hello, world!</h1>;
```

### 第二板斧：组件 (Components)
组件就是**函数**。它接收数据（Props），返回 JSX（界面）。

**定义一个组件：**
```jsx
// Welcome.js
function Welcome(props) {
  return <h1>Hello, {props.name}</h1>;
}
```

**使用这个组件：**
```jsx
// App.js
function App() {
  return (
    <div>
      <Welcome name="Sara" />
      <Welcome name="Cahal" />
      <Welcome name="Edite" />
    </div>
  );
}
```

### 第三板斧：Hooks (钩子)
让组件拥有“记忆”和“超能力”。最常用的是 `useState` 和 `useEffect`。

1.  **`useState`：让组件有记忆 (状态)**
    *   比如记录按钮被点击了多少次。
    ```jsx
    import React, { useState } from 'react';

    function Counter() {
      // 声明一个叫 count 的状态变量，初始值为 0
      const [count, setCount] = useState(0);

      return (
        <div>
          <p>你点击了 {count} 次</p>
          {/* 点击时调用 setCount 更新状态，界面会自动刷新 */}
          <button onClick={() => setCount(count + 1)}>
            点我 +1
          </button>
        </div>
      );
    }
    ```

2.  **`useEffect`：处理副作用 (Side Effects)**
    *   比如组件加载完后去请求 API 数据，或者手动修改网页标题。
    ```jsx
    import React, { useState, useEffect } from 'react';

    function UserProfile({ userId }) {
      const [user, setUser] = useState(null);

      // 当 userId 变化时，自动执行这里的代码
      useEffect(() => {
        // 模拟 API 请求
        fetch(`/api/user/${userId}`)
          .then(res => res.json())
          .then(data => setUser(data));
      }, [userId]); // 依赖项数组：userId 变了才重新执行

      if (!user) return <div>加载中...</div>;
      return <div>用户: {user.name}</div>;
    }
    ```

## 4. 实战演练：在本项目中怎么写？

在 `proteinx_infra` 的前端 (`frontend` 目录) 中，我们已经搭好了架子。

1.  **新建组件**：
    在 `src/components` 下新建 `MyCard.tsx`。
    ```tsx
    // src/components/MyCard.tsx
    import React from 'react';
    import { Card } from 'antd'; // 使用 Ant Design 组件库

    interface Props {
      title: string;
      content: string;
    }

    const MyCard: React.FC<Props> = ({ title, content }) => {
      return (
        <Card title={title} bordered={false} style={{ width: 300 }}>
          <p>{content}</p>
        </Card>
      );
    };
    export default MyCard;
    ```

2.  **在页面中使用**：
    打开 `src/pages/Dashboard/index.tsx`，引入并使用它。
    ```tsx
    import MyCard from '../../components/MyCard';

    // ... 在 return 里 ...
    <div style={{ display: 'flex', gap: '20px' }}>
      <MyCard title="任务 A" content="正在训练中..." />
      <MyCard title="任务 B" content="已完成" />
    </div>
    ```

3.  **看效果**：
    运行 `npm run dev`，浏览器会自动显示更新后的卡片。

## 5. 总结
*   **React 是**：用 JS 写界面的库。
*   **作用**：组件化开发（积木式）、数据驱动视图（改数据自动刷界面）。
*   **怎么用**：
    1.  用 **JSX** 写界面结构。
    2.  用 **Component** 封装功能块。
    3.  用 **useState** 管理数据变化。
    4.  用 **useEffect** 处理 API 请求。
