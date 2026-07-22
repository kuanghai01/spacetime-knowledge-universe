# 🚀 部署到 EdgeOne Pages + Render 后端

## 架构

```
EdgeOne Pages（前端）  ←→  Render.com（后端 API + WebSocket）
    静态 HTML/JS          Python FastAPI（免费 tier）
    全球边缘加速            国内访问加速
```

---

## 前置条件

1. **腾讯云账号**：https://cloud.tencent.com（有免费额度）
2. **GitHub 账号**：https://github.com
3. **Render 账号**：https://render.com（免费 tier）

---

## 第一步：推送到 GitHub

```bash
cd ~/.qclaw/workspace/spacetime-knowledge-universe

# 确保 .gitignore 存在
cat .gitignore >> /dev/null 2>&1 || echo "__pycache__/" > .gitignore

# 提交并推送
git init
git add .
git commit -m "v1.0 - 时空知识宇宙"
git branch -M main
git remote add origin https://github.com/你的用户名/spacetime-knowledge-universe.git
git push -u origin main
```

---

## 第二步：部署后端到 Render

1. 登录 https://render.com
2. **New +** → **Web Service** → 选择 GitHub 仓库
3. 配置：
   - **Name**: `spacetime-universe-api`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r render-requirements.txt`
   - **Start Command**: `uvicorn render_main:app --host 0.0.0.0 --port 10000`
   - **Plan**: Free
4. 部署完成后会得到一个 URL，例如：
   ```
   https://spacetime-universe-api.onrender.com
   ```

---

## 第三步：配置前端 API 地址

设置前端连接到 Render 后端。编辑 `frontend/index.html`：

```javascript
const API_BASE = 'https://spacetime-universe-api.onrender.com';
```

编辑 `frontend/shop.html` 同样修改 `API_BASE`。

提交：

```bash
git add frontend/
git commit -m "配置后端 API 地址"
git push
```

---

## 第四步：部署到 EdgeOne Pages

1. 登录 **腾讯云控制台**：https://console.cloud.tencent.com
2. 进入 **边缘安全加速平台 EO** → **Pages**
3. 点击 **立即使用** / **开通服务**（首次使用需开通）
4. 点击 **创建项目**
5. 选择数据源：
   - **方式 A：GitHub 一键部署**（推荐）
     - 授权 GitHub 账号
     - 选择 `spacetime-knowledge-universe` 仓库
     - 选择 `main` 分支
     - 构建命令：留空（纯静态文件，无需构建）
     - 输出目录：`frontend`
   - **方式 B：手动上传 ZIP**
     - 将 `frontend/` 文件夹打包为 ZIP
     - 上传到 EdgeOne Pages
6. 点击 **创建**，等待部署完成（约 1-2 分钟）

部署完成后，EdgeOne Pages 会提供一个默认域名：
```
https://你的项目名.edgeone.app
```

---

## 第五步：绑定自定义域名（可选）

如果你有域名，可以绑定：

1. EdgeOne Pages → 你的项目 → **自定义域名**
2. 输入你的域名，例如 `learn.yourdomain.com`
3. 按提示添加 DNS CNAME 解析：
   - 主机记录：`learn`
   - 记录类型：`CNAME`
   - 记录值：EdgeOne 提供的目标地址
4. 等待 DNS 生效（通常几分钟到几小时）
5. EdgeOne 自动配置 HTTPS 证书

---

## 第六步：测试

1. 打开 EdgeOne Pages 域名
2. 选择学科（历史/物理/数学）
3. 点击「开始学习」
4. 系统出题 → 你回答 → 系统反馈
5. 测试积分商城

---

## 常见问题

### Q: EdgeOne Pages 免费吗？
A: 有免费额度，个人使用完全够用。超出后按量付费，费用很低。

### Q: 国内访问速度快吗？
A: 非常快。EdgeOne 在全国有边缘节点，静态资源就近加载，延迟通常在 50ms 以内。

### Q: Render 后端在国内访问慢吗？
A: Render 服务器在海外，国内首次请求可能有 1-3 秒延迟。如果经常使用，建议考虑国内云服务器（约 50 元/月）。

### Q: 需要备案吗？
A: 如果使用 EdgeOne Pages 默认域名（.edgeone.app），不需要备案。如果使用自定义域名且服务器在中国大陆，需要备案。

### Q: 如何更新代码？
A: 本地修改后 `git push`，EdgeOne Pages 会自动重新部署。Render 也会自动重新部署。

### Q: WebSocket 在 EdgeOne 上能用吗？
A: 能。EdgeOne 支持 WebSocket 代理。

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `render_main.py` | Render 精简版入口 |
| `render-requirements.txt` | 精简版依赖 |
| `render.yaml` | Render 部署配置 |
| `frontend/index.html` | 学习页面（EdgeOne Pages 托管） |
| `frontend/shop.html` | 商城页面（EdgeOne Pages 托管） |
| `src/models/schemas.py` | 纯 Pydantic 模型 |
| `.github/workflows/pages.yml` | GitHub Actions（备用） |
