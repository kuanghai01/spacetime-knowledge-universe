# 时空知识宇宙

<div align="center">

🌌 **时空知识宇宙** 🌌

*游戏化沉浸式 AI 学习系统*

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-orange.svg)](https://langchain.com)

</div>

---

## 🎯 项目简介

「时空知识宇宙」是一个革命性的 AI 学习系统，通过**多智能体协作**、**游戏化激励**和**教材智能解析**，将枯燥的学习变成一场引人入胜的时空冒险。

### ✨ 核心特色

- 🤖 **智能导师系统**: 中枢校长 Agent 智能路由，各学科专家 Agent 个性化教学
- 🎮 **游戏化学习**: 积分、成就、学伴养成，让学习充满动力
- 📚 **教材智能解析**: 自动解析主流教材，生成知识图谱
- 🌉 **跨学科融合**: 打破学科壁垒，培养综合思维
- 🔌 **热插拔扩展**: 新学科即插即用，无需系统升级

## 🚀 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Milvus 2.3+ (向量数据库)
- Neo4j 5+ (知识图谱)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-org/spacetime-knowledge-universe.git
cd spacetime-knowledge-universe
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 填入你的配置
```

5. **启动服务**
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

6. **访问文档**

打开浏览器访问: http://localhost:8000/docs

## 📁 项目结构

```
spacetime-knowledge-universe/
├── docs/                    # 文档
│   └── ARCHITECTURE.md      # 架构设计文档
├── public/                  # 前端
│   └── index.html           # 学习助手页面
├── src/
│   ├── api/                 # API 路由
│   │   ├── learn.py         # 学习相关接口 + WebSocket
│   │   ├── users.py         # 用户相关接口
│   │   ├── gamification.py  # 游戏化接口
│   │   └── textbooks.py     # 教材解析接口
│   ├── agents/              # 学科 Agent
│   │   ├── base_agent.py    # Agent 基类
│   │   ├── history_agent.py # 历史 Agent
│   │   └── physics_agent.py # 物理 Agent
│   ├── core/                # 核心模块
│   │   ├── router/          # 路由层
│   │   │   └── principal_agent.py  # 中枢校长
│   │   ├── gamification/    # 游戏化引擎
│   │   │   └── engine.py
│   │   └── parser/          # 教材解析
│   │       └── textbook_parser.py
│   ├── models/              # 数据模型
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── subject.py
│   │   └── gamification.py
│   └── main.py              # 主入口
├── config/
│   └── settings.py          # 配置管理
├── tests/                   # 测试
├── scripts/
│   └── init_db.sql          # 数据库初始化
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 🎮 核心概念

### 中枢校长 Agent

负责意图识别和学科路由，将用户请求分发到正确的学科 Agent。

```python
principal = get_principal_agent()
result = await principal.handle_message(user_id, "秦始皇是哪年统一六国的？")
# 自动路由到历史 Agent
```

### 学科 Agent

每个学科有独立的 Agent，拥有专属知识库和教学策略。

**历史 Agent** — 故事化教学，带领学生穿越时空：
```python
history_agent = get_history_agent()
response = await history_agent.handle("秦始皇统一六国", context)
```

**物理 Agent** — 虚拟实验室，通过实验探索原理：
```python
physics_agent = get_physics_agent()
response = await physics_agent.handle("光的反射定律", context)
# 自动触发虚拟实验演示
```

**数学 Agent** — 可视化推理，让抽象变具象：
```python
math_agent = get_math_agent()
response = await math_agent.handle("解方程2x+5=13", context)
# 自动引导可视化推理
```

### 游戏化引擎

积分、成就、任务、排行榜，让学习充满动力。

```python
engine = get_gamification_engine()
result = await engine.process_study_activity(user_id, activity)
```

## 🔌 添加新学科

1. 创建新的 Agent 类（继承 `SubjectAgentBase`）
2. 实现知识库接口
3. 在主入口注册 Agent

```python
# src/agents/physics_agent.py
class PhysicsAgent(SubjectAgentBase):
    subject_id = "physics"
    subject_name = "物理"
    # ...

# src/main.py
principal.register_agent("physics", get_physics_agent())
```

## 📊 API 示例

### 学习对话

```bash
# WebSocket 连接（实时对话）
ws://localhost:8000/api/v1/learn/ws/history?user_id=xxx

# 发送消息
{"type": "question", "content": "秦始皇是哪年统一六国的？"}

# 接收响应
{
  "type": "answer",
  "content": "让我们穿越回公元前221年...",
  "related_knowledge": [...],
  "exp_gained": 15,
  "metadata": {"subject": "history", "agent": "史博士"}
}
```

### 前端页面

```bash
# 浏览器打开（支持 WebSocket 实时对话）
http://localhost:8000/
```

### 签到

```bash
POST /api/v1/gamification/checkin
Authorization: Bearer <token>

# 响应
{
  "success": true,
  "streak_days": 3,
  "exp_gained": 20,
  "message": "已连续学习 3 天，继续保持！"
}
```

## 🛣️ 开发路线图

- [x] **V0.1**: 基础架构 + 历史 Agent MVP
- [x] **V0.2**: 教材智能解析（PDF 提取 + 知识点提取）
- [x] **V0.3**: 知识库搜索 + 教材解析 API
- [x] **V0.4**: 物理 Agent + 虚拟实验室
- [x] **V0.5**: WebSocket 学习会话 + 前端页面
- [x] **V0.6**: 数学 Agent + 可视化推理
- [x] **V0.7**: Neo4j 知识图谱集成
- [x] **V1.0**: 积分商城 + 用户资产 + 部署文档 🎉

---

## 🚀 快速启动

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

<div align="center">

*让学习成为一场精彩的冒险* 🚀

</div>
