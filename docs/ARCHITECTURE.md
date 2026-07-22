# 时空知识宇宙 - 技术架构设计文档

> 版本: v1.0.0  
> 创建时间: 2026-07-21  
> 状态: 设计阶段

---

## 1. 系统概述

### 1.1 核心定位
「时空知识宇宙」是一个游戏化沉浸式 AI 学习系统，通过多智能体协作、动态学科扩展、教材智能解析，将学习转化为内在驱动力。

### 1.2 设计原则
- **模块化**: 各学科 Agent 物理隔离，支持热插拔
- **可扩展**: 新学科仅需上传知识库 + 配置规则
- **游戏化**: 积分、养成、任务替代传统打卡
- **精准化**: RAG 技术确保内容准确，避免幻觉

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户界面层 (Frontend)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Web App    │  │  Mobile App │  │  Mini Program│  │  API Client │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API 网关层 (Gateway)                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  认证鉴权 │ 限流控制 │ 请求路由 │ 日志追踪 │ WebSocket管理      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      中枢校长 Agent (Router Layer)                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  意图识别 │ 学科路由 │ 上下文管理 │ 跨学科协调 │ 用户状态管理    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│   历史 Agent        │ │   物理 Agent        │ │   数学 Agent        │
│  ┌───────────────┐  │ │  ┌───────────────┐  │ │  ┌───────────────┐  │
│  │ 知识库(隔离)  │  │ │  │ 知识库(隔离)  │  │ │  │ 知识库(隔离)  │  │
│  │ 教学策略      │  │ │  │ 教学策略      │  │ │  │ 教学策略      │  │
│  │ 任务生成器    │  │ │  │ 虚拟实验室    │  │ │  │ 解题引擎      │  │
│  └───────────────┘  │ │  └───────────────┘  │ │  └───────────────┘  │
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         共享服务层 (Shared Services)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ 用户资产    │  │ 游戏化引擎  │  │ 教材解析    │  │ 知识图谱    │   │
│  │ (积分/养成) │  │ (任务/成就) │  │ (PDF/NLP)   │  │ (Neo4j)     │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         数据存储层 (Storage)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ PostgreSQL  │  │   Redis     │  │  Milvus     │  │   Neo4j     │   │
│  │ (业务数据)  │  │ (缓存/会话) │  │ (向量检索)  │  │ (知识图谱)  │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心模块说明

| 模块 | 职责 | 技术选型 |
|------|------|----------|
| 中枢校长 Agent | 意图识别、学科路由、上下文管理 | LangChain + 自定义 Router |
| 学科 Agent | 学科教学、任务生成、知识问答 | LangChain Agent + RAG |
| 教材解析模块 | PDF 解析、知识点提取、知识图谱生成 | PyMuPDF + spaCy + GPT-4 |
| 游戏化引擎 | 积分计算、成就系统、任务链管理 | 自研规则引擎 |
| 知识图谱 | 概念关联、跨学科链接、学习路径推荐 | Neo4j + NetworkX |

---

## 3. 技术选型

### 3.1 后端技术栈

| 层次 | 技术 | 理由 |
|------|------|------|
| 语言 | Python 3.11+ | AI/ML 生态最完善 |
| Web 框架 | FastAPI | 高性能异步框架，原生支持 WebSocket |
| Agent 框架 | LangChain + LangGraph | 成熟的多智能体编排方案 |
| LLM | OpenAI GPT-4 / Claude 3 | 复杂推理与生成能力 |
| 向量数据库 | Milvus / Qdrant | 高性能向量检索，支持 RAG |
| 关系数据库 | PostgreSQL | 事务支持、JSON 字段、扩展性 |
| 缓存 | Redis | 会话管理、排行榜、限流 |
| 知识图谱 | Neo4j | 原生图数据库，支持复杂关系查询 |
| 消息队列 | RabbitMQ / Redis Streams | 异步任务处理 |

### 3.2 前端技术栈（建议）

| 技术 | 用途 |
|------|------|
| React 18 + TypeScript | Web 应用 |
| Next.js 14 | SSR + API Routes |
| TailwindCSS + shadcn/ui | UI 组件 |
| Zustand | 状态管理 |
| Socket.io | 实时通信 |

### 3.3 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Kubernetes Cluster                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ API Gateway │  │ Router Agent│  │ Subject x N │         │
│  │   (Ingress) │  │   (Deployment)│ │ (Deployment)│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ PostgreSQL  │  │   Redis     │  │   Milvus    │         │
│  │  (Stateful) │  │  (Stateful) │  │  (Stateful) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 数据模型设计

### 4.1 用户资产（全局共享）

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    avatar_url TEXT,
    level INT DEFAULT 1,
    exp BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 用户学科进度
CREATE TABLE user_subject_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    subject_id VARCHAR(50) NOT NULL,  -- 'history', 'physics', 'math'
    chapter_id VARCHAR(100),
    mastery_level INT DEFAULT 0,      -- 0-100 掌握度
    total_exp BIGINT DEFAULT 0,
    last_study_at TIMESTAMPTZ,
    UNIQUE(user_id, subject_id)
);

-- 积分/货币系统
CREATE TABLE user_currency (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    currency_type VARCHAR(50) NOT NULL,  -- 'knowledge_coin', 'energy', 'gem'
    amount BIGINT DEFAULT 0,
    UNIQUE(user_id, currency_type)
);

-- 成就系统
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url TEXT,
    condition_type VARCHAR(50),  -- 'study_hours', 'streak_days', 'mastery_level'
    condition_value INT,
    reward_exp INT,
    reward_currency JSONB
);

CREATE TABLE user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    achievement_id UUID REFERENCES achievements(id),
    unlocked_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);
```

### 4.2 学科知识库（物理隔离）

```sql
-- 学科配置表
CREATE TABLE subjects (
    id VARCHAR(50) PRIMARY KEY,  -- 'history', 'physics'
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url TEXT,
    agent_config JSONB,  -- Agent 配置
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 教材版本
CREATE TABLE textbooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id VARCHAR(50) REFERENCES subjects(id),
    publisher VARCHAR(100),      -- '人教版', '苏教版'
    grade VARCHAR(50),           -- '七年级', '八年级'
    version_year INT,
    file_path TEXT,
    parsed_data JSONB,           -- 解析后的结构化数据
    status VARCHAR(20) DEFAULT 'pending'  -- pending, parsing, ready, error
);

-- 知识点（每个学科独立 schema）
CREATE TABLE knowledge_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id VARCHAR(50) NOT NULL,
    textbook_id UUID REFERENCES textbooks(id),
    chapter_id VARCHAR(100),
    section_id VARCHAR(100),
    title VARCHAR(200) NOT NULL,
    content TEXT,
    difficulty INT,  -- 1-5
    tags TEXT[],
    embedding VECTOR(1536),  -- pgvector 或迁移到 Milvus
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 为每个学科创建分区表（物理隔离示例）
-- CREATE TABLE knowledge_points_history PARTITION OF knowledge_points FOR VALUES IN ('history');
-- CREATE TABLE knowledge_points_physics PARTITION OF knowledge_points FOR VALUES IN ('physics');
```

### 4.3 游戏化系统

```sql
-- 任务系统
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id VARCHAR(50) NOT NULL,
    type VARCHAR(50),  -- 'daily', 'weekly', 'chapter', 'cross_subject'
    title VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty INT,
    reward_exp INT,
    reward_currency JSONB,
    conditions JSONB,  -- 完成条件
    is_active BOOLEAN DEFAULT true
);

-- 用户任务进度
CREATE TABLE user_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    task_id UUID REFERENCES tasks(id),
    status VARCHAR(20) DEFAULT 'pending',  -- pending, in_progress, completed
    progress JSONB,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 学习记录（用于分析薄弱点）
CREATE TABLE study_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    subject_id VARCHAR(50) NOT NULL,
    knowledge_point_id UUID,
    activity_type VARCHAR(50),  -- 'quiz', 'reading', 'experiment', 'discussion'
    score INT,  -- 正确率或完成度
    time_spent INT,  -- 秒
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 养成系统（学伴/宠物）
CREATE TABLE user_companions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    companion_type VARCHAR(50),  -- 'scholar_cat', 'wizard_owl'
    name VARCHAR(100),
    level INT DEFAULT 1,
    exp BIGINT DEFAULT 0,
    mood INT DEFAULT 100,  -- 0-100
    appearance JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.4 知识图谱（Neo4j）

```cypher
// 知识点节点
CREATE (kp:KnowledgePoint {
    id: 'kp_001',
    subject: 'history',
    title: '秦始皇统一六国',
    chapter: '第三章',
    difficulty: 3,
    embedding: [0.1, 0.2, ...]
})

// 关联关系
CREATE (kp1)-[:PREREQUISITE_OF]->(kp2)  // 前置知识
CREATE (kp1)-[:RELATED_TO]->(kp3)       // 相关概念
CREATE (kp1)-[:CROSS_SUBJECT {type: 'geography'}]->(kp4)  // 跨学科关联

// 用户学习状态
CREATE (u:User {id: 'user_001'})
CREATE (u)-[:STUDYING {mastery: 80, last_access: timestamp()}]->(kp)
```

---

## 5. API 设计

### 5.1 核心 API 端点

```yaml
# 认证
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh

# 用户
GET  /api/v1/users/me
PUT  /api/v1/users/me
GET  /api/v1/users/me/progress
GET  /api/v1/users/me/achievements

# 学科
GET  /api/v1/subjects                    # 获取所有学科
GET  /api/v1/subjects/{subject_id}       # 获取学科详情
GET  /api/v1/subjects/{subject_id}/chapters  # 获取章节列表

# 学习会话（WebSocket）
WS   /api/v1/learn/{subject_id}          # 进入学科学习
# 消息格式:
# -> {"type": "question", "content": "秦始皇是哪年统一六国的？"}
# <- {"type": "answer", "content": "...", "related_kp": [...], "task": {...}}

# 教材解析
POST /api/v1/textbooks/upload            # 上传教材
GET  /api/v1/textbooks/{id}/status       # 查询解析状态
GET  /api/v1/textbooks/{id}/knowledge-map  # 获取知识图谱

# 任务系统
GET  /api/v1/tasks/daily                 # 获取每日任务
GET  /api/v1/tasks/chapter/{chapter_id}  # 获取章节任务
POST /api/v1/tasks/{task_id}/complete    # 完成任务

# 游戏化
GET  /api/v1/gamification/leaderboard    # 排行榜
POST /api/v1/gamification/checkin        # 签到
GET  /api/v1/gamification/companion      # 获取学伴状态
```

### 5.2 中枢校长 Agent API

```python
# 路由请求示例
POST /api/v1/router/dispatch
{
    "user_id": "uuid",
    "message": "我想了解秦始皇统一六国的历史背景",
    "context": {
        "current_subject": null,
        "recent_topics": ["唐朝盛世", "宋朝经济"]
    }
}

# 响应
{
    "target_agent": "history",
    "confidence": 0.95,
    "session_id": "sess_xxx",
    "context_injection": {
        "user_level": 3,
        "weak_points": ["秦朝制度"],
        "suggested_approach": "storytelling"
    }
}
```

---

## 6. 智能体架构

### 6.1 中枢校长 Agent

```python
class PrincipalAgent:
    """中枢校长：意图识别 + 学科路由 + 跨学科协调"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.subject_router = SubjectRouter()
        self.context_manager = ContextManager()
        self.cross_subject_coordinator = CrossSubjectCoordinator()
    
    async def dispatch(self, user_message: str, user_context: dict) -> DispatchResult:
        # 1. 意图识别
        intent = await self.intent_classifier.classify(user_message)
        
        # 2. 学科路由
        if intent.type == "subject_learning":
            target_subject = await self.subject_router.route(
                message=user_message,
                user_progress=user_context.progress,
                available_subjects=user_context.unlocked_subjects
            )
            return DispatchResult(
                target_agent=target_subject,
                mode="single_subject",
                context=self.context_manager.build_context(user_context)
            )
        
        # 3. 跨学科任务
        elif intent.type == "cross_subject_challenge":
            subjects = await self.cross_subject_coordinator.find_related_subjects(
                topic=intent.topic
            )
            return DispatchResult(
                target_agents=subjects,
                mode="cross_subject",
                context=self.cross_subject_coordinator.build_challenge(intent)
            )
```

### 6.2 学科 Agent 模板

```python
class SubjectAgentBase:
    """学科 Agent 基类"""
    
    def __init__(self, subject_id: str, knowledge_base: KnowledgeBase):
        self.subject_id = subject_id
        self.knowledge_base = knowledge_base
        self.llm = ChatOpenAI(model="gpt-4")
        self.memory = ConversationBufferMemory()
        self.task_generator = TaskGenerator(subject_id)
    
    async def handle(self, message: str, context: dict) -> AgentResponse:
        # 1. RAG 检索相关知识
        relevant_kps = await self.knowledge_base.search(
            query=message,
            filters={"subject": self.subject_id, "difficulty": context.user_level}
        )
        
        # 2. 构建 prompt
        prompt = self.build_teaching_prompt(
            user_message=message,
            knowledge_points=relevant_kps,
            user_profile=context.user_profile
        )
        
        # 3. 生成回复
        response = await self.llm.agenerate([prompt])
        
        # 4. 触发任务/成就检查
        await self.check_achievements(context.user_id, response)
        
        return AgentResponse(
            content=response.text,
            related_knowledge=relevant_kps,
            suggested_task=self.task_generator.suggest_next(relevant_kps)
        )
```

---

## 7. 教材智能解析模块

### 7.1 解析流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  PDF 上传   │───▶│  文本提取   │───▶│  结构识别   │───▶│  知识点提取 │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                  │
                    ┌─────────────┐    ┌─────────────┐           │
                    │  知识图谱   │◀───│  向量化存储 │◀──────────┘
                    │  构建       │    │  (Embedding)│
                    └─────────────┘    └─────────────┘
```

### 7.2 核心代码

```python
class TextbookParser:
    """教材智能解析器"""
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()  # PyMuPDF
        self.structure_recognizer = StructureRecognizer()  # 章节/标题识别
        self.knowledge_extractor = KnowledgeExtractor()  # NLP + LLM
        self.embedding_model = OpenAIEmbeddings()
    
    async def parse(self, pdf_path: str, subject_id: str) -> ParseResult:
        # 1. 提取文本
        raw_text = self.pdf_extractor.extract(pdf_path)
        
        # 2. 识别结构（章节、标题层级）
        structure = self.structure_recognizer.recognize(raw_text)
        
        # 3. 提取知识点
        knowledge_points = []
        for section in structure.sections:
            kps = await self.knowledge_extractor.extract(
                content=section.content,
                subject=subject_id,
                section_info=section.metadata
            )
            knowledge_points.extend(kps)
        
        # 4. 生成向量
        for kp in knowledge_points:
            kp.embedding = await self.embedding_model.embed(kp.content)
        
        # 5. 构建知识图谱关系
        graph = self.build_knowledge_graph(knowledge_points)
        
        return ParseResult(
            structure=structure,
            knowledge_points=knowledge_points,
            knowledge_graph=graph
        )
    
    def build_knowledge_graph(self, kps: List[KnowledgePoint]) -> KnowledgeGraph:
        """构建知识点之间的关联关系"""
        graph = KnowledgeGraph()
        
        for kp in kps:
            graph.add_node(kp)
            
            # 基于章节顺序建立前置关系
            # 基于语义相似度建立关联关系
            # 基于标签建立跨学科关联
            
        return graph
```

---

## 8. 游戏化引擎

### 8.1 核心机制

```python
class GamificationEngine:
    """游戏化引擎"""
    
    def __init__(self):
        self.exp_calculator = ExpCalculator()
        self.achievement_checker = AchievementChecker()
        self.task_manager = TaskManager()
        self.companion_system = CompanionSystem()
    
    async def record_study_activity(self, user_id: str, activity: StudyActivity):
        # 1. 计算经验值
        exp_gained = self.exp_calculator.calculate(activity)
        await self.add_exp(user_id, exp_gained)
        
        # 2. 检查成就解锁
        new_achievements = await self.achievement_checker.check(user_id, activity)
        if new_achievements:
            await self.notify_achievements(user_id, new_achievements)
        
        # 3. 更新任务进度
        await self.task_manager.update_progress(user_id, activity)
        
        # 4. 学伴互动
        await self.companion_system.react(user_id, activity)
    
    def calculate_mastery(self, user_id: str, knowledge_point_id: str) -> int:
        """计算知识点掌握度"""
        records = self.get_study_records(user_id, knowledge_point_id)
        # 基于正确率、复习次数、时间间隔计算
        return self.mastery_algorithm(records)
```

### 8.2 经验值公式

```python
# 基础经验值 = 知识点难度 * 10
# 加成系数:
#   - 连续学习: 1.0 + 0.1 * consecutive_days (max 2.0)
#   - 首次掌握: 1.5
#   - 完美答题: 1.2
#   - 跨学科关联: 1.3

def calculate_exp(activity: StudyActivity) -> int:
    base_exp = activity.knowledge_point.difficulty * 10
    
    multiplier = 1.0
    multiplier += min(0.1 * activity.consecutive_days, 1.0)  # 连续加成
    if activity.is_first_mastery:
        multiplier *= 1.5
    if activity.accuracy == 1.0:
        multiplier *= 1.2
    if activity.cross_subject_links:
        multiplier *= 1.3
    
    return int(base_exp * multiplier)
```

---

## 9. 部署与运维

### 9.1 环境配置

```yaml
# docker-compose.yml (开发环境)
version: '3.8'

services:
  api:
    build: ./src
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/spacetime
      - REDIS_URL=redis://redis:6379
      - MILVUS_HOST=milvus
      - NEO4J_URI=bolt://neo4j:7687
    depends_on:
      - postgres
      - redis
      - milvus
      - neo4j

  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: spacetime
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

  milvus:
    image: milvusdb/milvus:v2.3.0
    ports:
      - "19530:19530"

  neo4j:
    image: neo4j:5-community
    environment:
      NEO4J_AUTH: neo4j/password
    volumes:
      - neo4jdata:/data

volumes:
  pgdata:
  redisdata:
  neo4jdata:
```

### 9.2 监控与日志

- **APM**: Prometheus + Grafana
- **日志**: ELK Stack 或 Loki
- **追踪**: Jaeger (分布式追踪)
- **告警**: AlertManager

---

## 10. 开发路线图

### Phase 1: MVP (4周)
- [x] 项目架构搭建
- [ ] 中枢校长 Agent 基础路由
- [ ] 历史 Agent MVP
- [ ] 用户系统 + 基础积分
- [ ] 简单的知识问答

### Phase 2: 核心功能 (6周)
- [ ] 教材解析模块
- [ ] 游戏化系统完善
- [ ] 物理 Agent 上线
- [ ] 知识图谱可视化
- [ ] 任务链系统

### Phase 3: 扩展优化 (4周)
- [ ] 数学 Agent
- [ ] 跨学科任务
- [ ] 学伴养成系统
- [ ] 移动端适配
- [ ] 性能优化

### Phase 4: 规模化 (持续)
- [ ] 更多学科支持
- [ ] AI 出题引擎
- [ ] 社交系统
- [ ] 多地区教材适配

---

## 11. 风险与应对

| 风险 | 影响 | 应对策略 |
|------|------|----------|
| LLM 幻觉 | 高 | RAG 强化 + 知识点锚定 + 人工审核 |
| 教材版权 | 高 | 使用开放教育资源 + 合作授权 |
| 多 Agent 协调复杂度 | 中 | 标准化接口 + 充分测试 |
| 知识图谱维护成本 | 中 | 半自动构建 + 社区贡献 |
| 用户留存 | 中 | 持续游戏化迭代 + 社交机制 |

---

## 附录

### A. 术语表
- **RAG**: Retrieval-Augmented Generation，检索增强生成
- **Knowledge Point**: 知识点，最小学习单元
- **Mastery Level**: 掌握度，0-100 表示对知识点的熟悉程度

### B. 参考资料
- LangChain 文档: https://python.langchain.com/
- Neo4j 图数据库: https://neo4j.com/docs/
- Milvus 向量数据库: https://milvus.io/docs/
