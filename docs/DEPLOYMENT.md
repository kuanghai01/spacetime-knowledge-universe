# 部署指南

## 快速启动

### 标准模式（全部功能）

```bash
# 1. 克隆项目
cd spacetime-knowledge-universe

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动 Neo4j（Docker）
docker-compose up -d neo4j

# 5. 填充知识图谱种子数据
curl -X POST http://localhost:8000/api/v1/kg/seed

# 6. 启动应用
OPENAI_API_KEY=your_key uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 7. 访问
# 前端:    http://localhost:8000/
# 商城:    http://localhost:8000/shop.html
# API文档: http://localhost:8000/docs
```

### 轻量模式（无 Neo4j/Milvus）

```bash
# 直接启动，知识图谱和向量检索会自动降级
OPENAI_API_KEY=your_key uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 演示模式（无 API Key）

```bash
# 不设置 OPENAI_API_KEY，系统会返回预设的演示响应
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

## Docker Compose 完整部署

```bash
# 启动全部服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 填充种子数据
docker-compose exec api curl -X POST http://localhost:8000/api/v1/kg/seed
```

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_KEY` | - | OpenAI API Key（可选，不填则演示模式） |
| `OPENAI_MODEL` | gpt-4o-mini | 模型名称 |
| `NEO4J_URI` | bolt://localhost:7687 | Neo4j 连接地址 |
| `NEO4J_USER` | neo4j | Neo4j 用户名 |
| `NEO4J_PASSWORD` | password | Neo4j 密码 |
| `NEO4J_DATABASE` | neo4j | Neo4j 数据库名 |
| `REDIS_URL` | redis://localhost:6379 | Redis 连接地址 |
| `POSTGRES_DSN` | postgresql://user:pass@localhost/skuniverse | PostgreSQL 连接串 |
| `API_V1_PREFIX` | /api/v1 | API 前缀 |
| `DEBUG` | false | 调试模式 |

---

## 系统架构

```
                    ┌──────────────────────────────┐
                    │       Frontend (HTML/CSS/JS)  │
                    │   /public/index.html          │
                    │   /public/shop.html           │
                    └──────────────┬───────────────┘
                                   │ HTTP / WebSocket
                    ┌──────────────▼───────────────┐
                    │     FastAPI Gateway           │
                    │     uvicorn :8000             │
                    ├──────────────────────────────┤
                    │ │ API Routers:                │
                    │ │  /api/v1/learn/*   (学习)    │
                    │ │  /api/v1/shop/*    (商城)    │
                    │ │  /api/v1/kg/*      (知识图谱)│
                    │ │  /api/v1/assets/*  (资产)    │
                    │ └────────────────────────────┤
                    ├──────────────────────────────┤
                    │  Core Services:               │
                    │  ├─ PrincipalAgent (路由)     │
                    │  ├─ KnowledgeGraphService     │
                    │  ├─ UserAssetService          │
                    │  ├─ PointsShop                │
                    │  └─ TextbookParser            │
                    ├──────────────────────────────┤
                    │  Agents:                      │
                    │  ├─ HistoryAgent (史博士)     │
                    │  ├─ PhysicsAgent (物先生)     │
                    │  └─ MathAgent   (数先生)      │
                    └──────────────┬───────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            │                      │                      │
   ┌────────▼──────┐    ┌─────────▼──────┐    ┌─────────▼──────┐
   │   Neo4j       │    │   PostgreSQL   │    │     Redis      │
   │  (知识图谱)    │    │   (业务数据)   │    │   (缓存)       │
   └───────────────┘    └────────────────┘    └────────────────┘
```

---

## 端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| FastAPI | 8000 | 应用主入口 |
| Neo4j HTTP | 7474 | Neo4j 浏览器 |
| Neo4j Bolt | 7687 | Neo4j 驱动连接 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存/会话 |

---

## 生产环境部署清单

- [ ] 设置强密码（Neo4j/PostgreSQL/Redis）
- [ ] 配置 CORS 白名单
- [ ] 配置 HTTPS/TLS
- [ ] 设置环境变量（DEBUG=false）
- [ ] 配置数据持久化卷
- [ ] 配置日志收集
- [ ] 配置监控/告警
- [ ] 设置自动备份
- [ ] 配置负载均衡（如多实例）
