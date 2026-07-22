# 快速启动指南

## 前置条件

- Python 3.11+
- Docker & Docker Compose（可选，用于完整环境）

## 方式一：本地开发（最小化）

### 1. 安装依赖

```bash
cd spacetime-knowledge-universe
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，至少填入 OPENAI_API_KEY
```

### 3. 启动服务

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 方式二：Docker 完整环境

### 1. 启动所有服务

```bash
docker-compose up -d
```

这会启动:
- 应用服务 (port 8000)
- PostgreSQL (port 5432)
- Redis (port 6379)
- Milvus (port 19530)
- Neo4j (port 7474/7687)

### 2. 查看日志

```bash
docker-compose logs -f app
```

### 3. 停止服务

```bash
docker-compose down
```

## 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_router.py -v
pytest tests/test_gamification.py -v
```

## API 快速测试

### 获取学科列表

```bash
curl http://localhost:8000/api/v1/subjects
```

### 用户登录

```bash
curl -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test123"
```

### 签到

```bash
curl -X POST http://localhost:8000/api/v1/gamification/checkin \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 添加新学科

1. 创建 Agent 文件 `src/agents/physics_agent.py`:

```python
from src.agents.base_agent import SubjectAgentBase

class PhysicsAgent(SubjectAgentBase):
    subject_id = "physics"
    subject_name = "物理"
    
    def get_system_prompt(self, context):
        return "你是一位物理导师..."
```

2. 在 `src/main.py` 注册:

```python
from src.agents.physics_agent import PhysicsAgent

physics_agent = PhysicsAgent()
principal.register_agent("physics", physics_agent)
```

## 常见问题

### Q: 没有 OPENAI_API_KEY 怎么办？

A: 可以修改 `config/settings.py` 使用其他 LLM 服务，或使用本地模型。

### Q: 数据库连接失败？

A: 确保 PostgreSQL 已启动，或改用 Docker 方式。

### Q: 如何查看知识图谱？

A: 访问 Neo4j Browser: http://localhost:7474

## 下一步

- [ ] 完善教材解析模块
- [ ] 添加更多学科 Agent
- [ ] 实现 WebSocket 学习会话
- [ ] 前端界面开发
