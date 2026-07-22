"""
学科 Agent 基类

所有学科 Agent 的抽象基类，定义统一的接口和通用功能。
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Agent 上下文"""
    user_id: str
    user_level: int = 1
    current_chapter: Optional[str] = None
    weak_points: list[str] = field(default_factory=list)
    recent_topics: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Agent 响应"""
    content: str
    related_knowledge: list[dict] = field(default_factory=list)
    suggested_task: Optional[dict] = None
    achievement_triggered: Optional[dict] = None
    exp_gained: int = 0
    metadata: dict = field(default_factory=dict)


class KnowledgeBase:
    """知识库接口（抽象）"""
    
    async def search(
        self,
        query: str,
        filters: dict = None,
        top_k: int = 5
    ) -> list[dict]:
        """搜索相关知识"""
        raise NotImplementedError
    
    async def get_by_id(self, kp_id: str) -> Optional[dict]:
        """根据 ID 获取知识点"""
        raise NotImplementedError
    
    async def get_chapter_knowledge(self, chapter_id: str) -> list[dict]:
        """获取章节知识"""
        raise NotImplementedError


class SubjectAgentBase(ABC):
    """
    学科 Agent 基类
    
    子类需要实现:
    - subject_id: 学科标识
    - subject_name: 学科名称
    - get_system_prompt: 获取系统提示词
    - get_teaching_strategy: 获取教学策略
    """
    
    # 子类必须定义
    subject_id: str = ""
    subject_name: str = ""
    
    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None):
        self.knowledge_base = knowledge_base
        self.llm = None
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.7,
                api_key=settings.OPENAI_API_KEY
            )
        self.conversation_history: dict[str, list[dict]] = {}  # user_id -> history
        
    @abstractmethod
    def get_system_prompt(self, context: AgentContext) -> str:
        """获取系统提示词（子类实现）"""
        pass
    
    def get_teaching_strategy(self, context: AgentContext) -> str:
        """获取教学策略（可覆盖）"""
        return """
教学原则:
1. 循序渐进，由浅入深
2. 联系生活实际，增加趣味性
3. 鼓励学生思考，适时提问
4. 及时肯定学生的进步
5. 发现薄弱点时，耐心讲解
"""
    
    async def handle(self, message: str, context: dict) -> dict:
        """
        处理用户消息
        
        Args:
            message: 用户消息
            context: 上下文信息
            
        Returns:
            响应字典
        """
        # 构建 Agent 上下文
        agent_context = AgentContext(
            user_id=context.get("user_id", "anonymous"),
            user_level=context.get("user_level", 1),
            current_chapter=context.get("current_chapter"),
            weak_points=context.get("weak_points", []),
            recent_topics=context.get("recent_topics", []),
        )
        
        # 1. RAG 检索相关知识
        relevant_knowledge = []
        if self.knowledge_base:
            relevant_knowledge = await self.knowledge_base.search(
                query=message,
                limit=5
            )
        
        # 2. 构建 prompt
        prompt = self._build_prompt(message, agent_context, relevant_knowledge)
        
        # 3. 调用 LLM（无 API key 时使用演示响应）
        if self.llm:
            response = await self.llm.ainvoke(prompt)
            content = response.content
        else:
            # 演示模式：基于知识库生成简单响应
            content = self._get_demo_response(message, relevant_knowledge)
        
        # 4. 解析响应，提取知识点引用
        parsed_response = self._parse_response(response.content, relevant_knowledge)
        
        # 5. 计算经验值
        exp_gained = self._calculate_exp(agent_context, parsed_response)
        
        # 6. 生成建议任务
        suggested_task = self._suggest_next_task(agent_context, relevant_knowledge)
        
        return {
            "content": parsed_response["content"],
            "related_knowledge": parsed_response["related_knowledge"],
            "suggested_task": suggested_task,
            "exp_gained": exp_gained,
            "metadata": {
                "subject": self.subject_id,
                "timestamp": datetime.now().isoformat(),
            }
        }
    
    def _get_demo_response(self, message: str, knowledge: list[dict]) -> str:
        """生成演示模式响应（无 API key 时）"""
        if knowledge:
            kp = knowledge[0]
            return f"**{kp.get('title', '知识点')}**\n\n{kp.get('content', '')[:200]}\n\n💡 *这是演示模式响应。要启用完整 AI 对话，请在 .env 中配置 OPENAI_API_KEY。*"
        return f"你问的是关于「{message}」的问题。\n\n这是一个演示模式响应。要启用完整 AI 对话，请在 .env 中配置 OPENAI_API_KEY。"
    
    def _build_prompt(
        self,
        message: str,
        context: AgentContext,
        knowledge: list[dict]
    ) -> list:
        """构建 LLM prompt"""
        
        system_prompt = self.get_system_prompt(context)
        teaching_strategy = self.get_teaching_strategy(context)
        
        # 构建知识上下文
        knowledge_context = ""
        if knowledge:
            knowledge_context = "\n\n【参考资料】\n"
            for i, kp in enumerate(knowledge, 1):
                knowledge_context += f"{i}. {kp.get('title', '')}: {kp.get('content', '')[:200]}...\n"
        
        # 用户画像
        user_profile = f"""
【学生画像】
- 当前等级: Lv.{context.user_level}
- 当前章节: {context.current_chapter or '未指定'}
- 薄弱点: {', '.join(context.weak_points) if context.weak_points else '暂无'}
"""
        
        full_system_prompt = f"""{system_prompt}

{teaching_strategy}
{user_profile}
{knowledge_context}

请用生动有趣的方式回答学生的问题，适当使用比喻和故事。回答后，可以提出一个引导性问题或建议下一步学习内容。"""
        
        # 获取对话历史
        history = self.conversation_history.get(context.user_id, [])[-5:]
        
        messages = [SystemMessage(content=full_system_prompt)]
        
        # 添加历史消息
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(SystemMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=message))
        
        return messages
    
    def _parse_response(self, content: str, knowledge: list[dict]) -> dict:
        """解析 LLM 响应"""
        # 简单的知识点匹配（实际可以用更复杂的 NLP）
        related_kp = []
        for kp in knowledge:
            title = kp.get("title", "")
            if title and title in content:
                related_kp.append({
                    "id": kp.get("id"),
                    "title": title,
                    "relevance": 0.8
                })
        
        return {
            "content": content,
            "related_knowledge": related_kp
        }
    
    def _calculate_exp(self, context: AgentContext, response: dict) -> int:
        """计算获得经验值"""
        base_exp = settings.BASE_EXP_PER_KNOWLEDGE
        
        # 根据知识点数量加成
        kp_bonus = len(response.get("related_knowledge", [])) * 2
        
        return base_exp + kp_bonus
    
    def _suggest_next_task(self, context: AgentContext, knowledge: list[dict]) -> Optional[dict]:
        """建议下一步任务"""
        if not knowledge:
            return None
        
        # 返回下一个知识点作为建议
        next_kp = knowledge[0] if knowledge else None
        if next_kp:
            return {
                "type": "knowledge_point",
                "title": f"继续学习: {next_kp.get('title', '')}",
                "knowledge_point_id": next_kp.get("id"),
            }
        return None
    
    def add_conversation(self, user_id: str, role: str, content: str):
        """添加对话历史"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # 保留最近 10 条
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
