# 🚀 部署指南（免费方案）

## 架构

```
GitHub Pages（前端）  ←→  Render.com（后端 API + WebSocket）
    静态 HTML/JS          Python FastAPI（免费 tier）
```

## 前置条件

1. **GitHub 账号**：https://github.com/signup
2. **Render 账号**：https://render.com（用 GitHub 账号登录）

---

## 第一步：创建 GitHub 仓库

1. 登录 GitHub，点击 **New repository**
2. 仓库名：`spacetime-knowledge-universe`
3. 不要勾选 Add a README（本地已有代码）
4. 点击 **Create repository**

---

## 第二步：推送代码

在项目目录执行：

```bash
cd ~/.qclaw/workspace/spacetime-knowledge-universe

# 初始化 Git（如果还没有）
git init
git add .
git commit -m "时空知识宇宙 v1.0 - 初始提交"

# 关联远程仓库（替换 YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/spacetime-knowledge-universe.git
git branch -M main
git push -u origin main
```

---

## 第三步：部署后端到 Render

### 方式 A：通过 Render Dashboard（推荐）

1. 登录 https://render.com
2. 点击 **New +** → **Web Service**
3. 选择 **Build and deploy from a Git repository**
4. 选择 `spacetime-knowledge-universe` 仓库
5. 配置：
   - **Name**: `spacetime-knowledge-universe`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r render-requirements.txt`
   - **Start Command**: `uvicorn render_main:app --host 0.0.0.0 --port 10000`
   - **Plan**: Free
6. 点击 **Create Web Service**
7. 等待部署完成（约 2-3 分钟）

### 方式 B：通过 render.yaml（一键部署）

仓库已包含 `render.yaml`，Render 会自动检测并部署。

---

## 第四步：配置前端 API 地址

部署完成后，Render 会给你一个 URL，例如：
```
https://spacetime-knowledge-universe-xxxx.onrender.com
```

修改 `frontend/index.html` 第 461 行：

```javascript
// 改为你的 Render 地址
const API_BASE = 'https://spacetime-knowledge-universe-xxxx.onrender.com';
```

修改 `frontend/shop.html` 第 223 行：

```javascript
const API_BASE = 'https://spacetime-knowledge-universe-xxxx.onrender.com';
```

提交并推送：

```bash
git add frontend/
git commit -m "配置 Render 后端地址"
git push
```

---

## 第五步：启用 GitHub Pages

1. 进入 GitHub 仓库 → **Settings** → **Pages**
2. **Source**: Deploy from a branch
3. **Branch**: `main` / `/frontend` 文件夹
4. 点击 **Save**
5. 等待 1-2 分钟，访问：
   ```
   https://YOUR_USERNAME.github.io/spacetime-knowledge-universe/
   ```

---

## 第六步：测试

1. 打开 GitHub Pages 地址
2. 选择学科（历史/物理/数学）
3. 点击「开始学习」
4. 系统出题 → 你回答 → 系统反馈
5. 测试积分商城

---

## 常见问题

### Q: Render 免费 tier 会休眠吗？
A: 会。15 分钟无请求后休眠，首次请求需等待 30-60 秒冷启动。这是免费 tier 的正常行为。

### Q: WebSocket 在 Render 上能用吗？
A: 能。Render 免费 tier 支持 WebSocket。

### Q: 需要配置 API Key 吗？
A: 不需要。系统内置演示模式，无 API Key 也能运行。如需完整 AI 功能，在 Render Dashboard 添加环境变量 `OPENAI_API_KEY`。

### Q: 国内访问 Render 慢吗？
A: 可能有些慢（1-3 秒延迟）。如果经常使用，建议考虑国内云服务器（约 50 元/月）。

### Q: 如何更新代码？
A: 本地修改后 `git push`，Render 会自动重新部署。GitHub Pages 也会自动更新。

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `render_main.py` | Render 精简版入口（无数据库依赖） |
| `render-requirements.txt` | 精简版依赖 |
| `render.yaml` | Render 部署配置 |
| `frontend/index.html` | 学习页面（GitHub Pages 托管） |
| `frontend/shop.html` | 商城页面（GitHub Pages 托管） |
| `src/models/schemas.py` | 纯 Pydantic 模型（无 SQLAlchemy） |
