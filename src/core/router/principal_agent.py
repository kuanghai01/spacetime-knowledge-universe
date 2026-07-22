"""
中枢校长 Agent - 智能路由层

负责:
1. 意图识别 - 判断用户消息属于哪个学科/功能
2. 学科路由 - 将请求分发到正确的学科 Agent
3. 上下文管理 - 维护用户学习会话状态
4. 跨学科协调 - 处理涉及多个学科的任务
"""
import logging
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.settings import settings

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """意图类型"""
    SUBJECT_LEARNING = "subject_learning"      # 学科学习
    CROSS_SUBJECT = "cross_subject"            # 跨学科任务
    GAMIFICATION = "gamification"              # 游戏化相关（签到、排行榜等）
    SYSTEM_CONTROL = "system_control"          # 系统控制（切换学科、设置等）
    GENERAL_CHAT = "general_chat"              # 闲聊


@dataclass
class UserContext:
    """用户上下文"""
    user_id: str
    current_subject: Optional[str] = None
    current_chapter: Optional[str] = None
    user_level: int = 1
    unlocked_subjects: list[str] = field(default_factory=lambda: ["history"])
    weak_points: list[str] = field(default_factory=list)
    recent_topics: list[str] = field(default_factory=list)
    conversation_history: list[dict] = field(default_factory=list)


@dataclass
class DispatchResult:
    """路由结果"""
    target_agent: str  # 目标学科 Agent ID
    target_agents: list[str] = field(default_factory=list)  # 跨学科时的多个 Agent
    mode: str = "single_subject"  # single_subject | cross_subject | system
    confidence: float = 0.0
    session_id: str = ""
    context_injection: dict = field(default_factory=dict)
    intent: IntentType = IntentType.SUBJECT_LEARNING


class IntentClassifier:
    """意图分类器"""
    
    SYSTEM_PROMPT = """你是「时空知识宇宙」的意图识别系统。
分析用户消息，判断其意图类型和目标学科。

意图类型:
- subject_learning: 学习某个学科的知识（历史、物理、数学、化学等）
- cross_subject: 涉及多个学科的综合性问题
- gamification: 签到、查看积分、排行榜、成就等
- system_control: 切换学科、选择教材、系统设置
- general_chat: 闲聊或与学习无关的对话

学科列表: {subjects}

请以 JSON 格式返回:
{{
    "intent_type": "意图类型",
    "target_subject": "目标学科（如果是学科学习）",
    "confidence": 0.0-1.0,
    "related_subjects": ["相关学科列表"]
}}
"""
    
    def __init__(self):
        self.llm = None
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.1,
                api_key=settings.OPENAI_API_KEY
            )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
    
    async def classify(self, message: str, history: list[dict] = None) -> dict:
        """分类用户意图"""
        if not self.llm:
            # 无 API key 时使用简单关键词匹配
            return self._keyword_classify(message)
        
        subjects_str = ", ".join(settings.AVAILABLE_SUBJECTS)
        
        chain = self.prompt | self.llm
        
        response = await chain.ainvoke({
            "subjects": subjects_str,
            "history": history or [],
            "input": message
        })
        
        # 解析 JSON 响应
        try:
            import json
            result = json.loads(response.content)
            return result
        except Exception as e:
            logger.warning(f"Failed to parse intent response: {e}")
            return self._keyword_classify(message)
    
    def _keyword_classify(self, message: str) -> dict:
        """关键词匹配分类（无 API key 时的 fallback）"""
        msg = message.lower()
        subjects = {
            "history": ["历史", "朝代", "皇帝", "古代", "秦始皇", "汉朝", "唐朝"],
            "physics": ["物理", "力", "光", "电", "运动", "牛顿", "能量"],
            "math": ["数学", "方程", "函数", "几何", "代数", "计算", "解题"],
        }
        for subject, keywords in subjects.items():
            if any(kw in msg for kw in keywords):
                return {
                    "intent_type": "subject_query",
                    "target_subject": subject,
                    "confidence": 0.7,
                    "related_subjects": [subject]
                }
        return {
            "intent_type": "general_chat",
            "target_subject": None,
            "confidence": 0.5,
            "related_subjects": []
        }


class SubjectRouter:
    """学科路由器"""
    
    def __init__(self):
        self.subject_agents = {
            "history": "history_agent",
            "physics": "physics_agent",
            "math": "math_agent",
            "chemistry": "chemistry_agent",
        }
    
    async def route(
        self,
        message: str,
        intent_result: dict,
        user_context: UserContext
    ) -> str:
        """路由到目标学科"""
        
        # 1. 如果意图明确指定了学科
        target_subject = intent_result.get("target_subject")
        if target_subject and target_subject in self.subject_agents:
            return target_subject
        
        # 2. 如果用户当前正在某个学科
        if user_context.current_subject:
            return user_context.current_subject
        
        # 3. 基于关键词的简单匹配（降级方案）
        keyword_mapping = {
            "history": ["历史", "朝代", "皇帝", "战争", "古代", "近代"],
            "physics": ["物理", "力学", "运动", "能量", "电学", "光学", "声学", "热学"],
            "math": ["数学", "函数", "几何", "代数", "算术"],
            "chemistry": ["化学", "元素", "分子", "反应", "化合物", "溶液"],
        }
        
        # 优先匹配更具体的关键词（避免"方程"匹配数学而"化学方程式"应匹配化学）
        specific_keywords = {
            "chemistry": ["化学方程式", "化学式", "化学变化"],
            "math": ["数学方程", "解方程", "方程式求解"],
        }
        for subject, keywords in specific_keywords.items():
            if any(kw in message for kw in keywords):
                return subject
        
        for subject, keywords in keyword_mapping.items():
            if any(kw in message for kw in keywords):
                return subject
        
        # 4. 默认返回历史（首个学科）
        return "history"


class ContextManager:
    """上下文管理器"""
    
    def __init__(self):
        self.sessions: dict[str, UserContext] = {}
    
    def get_context(self, user_id: str) -> UserContext:
        """获取用户上下文"""
        if user_id not in self.sessions:
            self.sessions[user_id] = UserContext(user_id=user_id)
        return self.sessions[user_id]
    
    def update_context(self, user_id: str, **kwargs):
        """更新用户上下文"""
        ctx = self.get_context(user_id)
        for key, value in kwargs.items():
            if hasattr(ctx, key):
                setattr(ctx, key, value)
    
    def build_context_for_agent(self, user_context: UserContext) -> dict:
        """构建传递给学科 Agent 的上下文"""
        return {
            "user_id": user_context.user_id,
            "user_level": user_context.user_level,
            "current_chapter": user_context.current_chapter,
            "weak_points": user_context.weak_points,
            "recent_topics": user_context.recent_topics[-5:],  # 最近5个话题
        }
    
    def add_conversation(self, user_id: str, role: str, content: str):
        """添加对话历史"""
        ctx = self.get_context(user_id)
        ctx.conversation_history.append({"role": role, "content": content})
        # 保留最近 20 条
        if len(ctx.conversation_history) > 20:
            ctx.conversation_history = ctx.conversation_history[-20:]


class CrossSubjectCoordinator:
    """跨学科协调器"""
    
    async def find_related_subjects(self, topic: str) -> list[str]:
        """找出与主题相关的学科"""
        # 简单的关键词匹配，实际可以用更复杂的语义分析
        cross_subject_map = {
            "丝绸之路": ["history", "geography", "economics"],
            "文艺复兴": ["history", "art", "science"],
            "工业革命": ["history", "physics", "chemistry", "economics"],
            "阿波罗登月": ["history", "physics", "math"],
        }
        
        for key, subjects in cross_subject_map.items():
            if key in topic:
                return subjects
        
        return ["history"]  # 默认
    
    def build_challenge(self, intent_result: dict) -> dict:
        """构建跨学科挑战"""
        return {
            "challenge_type": "cross_subject",
            "topic": intent_result.get("target_subject", ""),
            "related_subjects": intent_result.get("related_subjects", []),
        }


class PrincipalAgent:
    """
    中枢校长 Agent
    
    核心职责:
    1. 接收用户消息
    2. 识别意图
    3. 路由到正确的学科 Agent
    4. 管理跨学科任务
    """
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.subject_router = SubjectRouter()
        self.context_manager = ContextManager()
        self.cross_subject_coordinator = CrossSubjectCoordinator()
        
        # 学科 Agent 注册表（实际使用时注入）
        self.agent_registry: dict[str, any] = {}
    
    def register_agent(self, subject_id: str, agent: any):
        """注册学科 Agent"""
        self.agent_registry[subject_id] = agent
        logger.info(f"Registered agent for subject: {subject_id}")
    
    async def dispatch(self, user_id: str, message: str) -> DispatchResult:
        """
        分发用户消息到正确的 Agent
        
        Args:
            user_id: 用户 ID
            message: 用户消息
            
        Returns:
            DispatchResult: 路由结果
        """
        # 1. 获取用户上下文
        user_context = self.context_manager.get_context(user_id)
        
        # 2. 意图识别
        intent_result = await self.intent_classifier.classify(
            message=message,
            history=user_context.conversation_history[-5:]
        )
        
        logger.info(f"Intent classified: {intent_result}")
        
        # 3. 根据意图类型处理
        intent_type = IntentType(intent_result.get("intent_type", "general_chat"))
        
        if intent_type == IntentType.SUBJECT_LEARNING:
            # 路由到单个学科
            target_subject = await self.subject_router.route(
                message=message,
                intent_result=intent_result,
                user_context=user_context
            )
            
            # 更新用户当前学科
            self.context_manager.update_context(user_id, current_subject=target_subject)
            
            return DispatchResult(
                target_agent=target_subject,
                mode="single_subject",
                confidence=intent_result.get("confidence", 0.8),
                session_id=f"{user_id}_{target_subject}",
                context_injection=self.context_manager.build_context_for_agent(user_context),
                intent=intent_type
            )
        
        elif intent_type == IntentType.CROSS_SUBJECT:
            # 跨学科任务
            related_subjects = await self.cross_subject_coordinator.find_related_subjects(message)
            
            return DispatchResult(
                target_agent=related_subjects[0] if related_subjects else "history",
                target_agents=related_subjects,
                mode="cross_subject",
                confidence=intent_result.get("confidence", 0.7),
                session_id=f"{user_id}_cross",
                context_injection=self.cross_subject_coordinator.build_challenge(intent_result),
                intent=intent_type
            )
        
        elif intent_type == IntentType.GAMIFICATION:
            return DispatchResult(
                target_agent="system",
                mode="system",
                confidence=1.0,
                intent=intent_type
            )
        
        else:
            # 默认路由到当前学科或历史
            target_subject = user_context.current_subject or "history"
            return DispatchResult(
                target_agent=target_subject,
                mode="single_subject",
                confidence=0.5,
                intent=IntentType.GENERAL_CHAT
            )
    
    async def handle_message(self, user_id: str, message: str) -> dict:
        """
        处理用户消息的完整流程
        
        Returns:
            包含响应内容和元数据的结果
        """
        # 1. 路由
        dispatch_result = await self.dispatch(user_id, message)
        
        # 2. 记录用户消息
        self.context_manager.add_conversation(user_id, "user", message)
        
        # 3. 调用目标 Agent
        if dispatch_result.target_agent in self.agent_registry:
            agent = self.agent_registry[dispatch_result.target_agent]
            response = await agent.handle(
                message=message,
                context=dispatch_result.context_injection
            )
        else:
            # Agent 未注册，返回提示
            response = {
                "content": f"学科 {dispatch_result.target_agent} 正在准备中，敬请期待！",
                "related_knowledge": [],
                "suggested_task": None
            }
        
        # 4. 记录 AI 响应
        self.context_manager.add_conversation(user_id, "assistant", response.get("content", ""))
        
        return {
            "dispatch": dispatch_result,
            "response": response
        }


# 单例
_principal_agent: Optional[PrincipalAgent] = None


def get_principal_agent() -> PrincipalAgent:
    """获取中枢校长 Agent 单例"""
    global _principal_agent
    if _principal_agent is None:
        _principal_agent = PrincipalAgent()
    return _principal_agent
