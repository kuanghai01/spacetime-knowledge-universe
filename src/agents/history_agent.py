"""
历史学科 Agent

专注于历史教学，采用故事化、情境化的教学方式。
"""
import logging
from typing import Optional

from src.agents.base_agent import SubjectAgentBase, KnowledgeBase, AgentContext
from src.data.history_data import ALL_HISTORY_KNOWLEDGE

logger = logging.getLogger(__name__)


class HistoryKnowledgeBase(KnowledgeBase):
    """历史知识库——加载初中完整历史课程（120个知识点）"""

    def __init__(self):
        # 从数据模块加载完整知识库
        self.knowledge_points = [kp.copy() for kp in ALL_HISTORY_KNOWLEDGE]
    
    async def search(self, query: str, filters: dict = None, top_k: int = 5) -> list[dict]:
        """简单的关键词搜索"""
        results = []
        query_lower = query.lower()
        
        for kp in self.knowledge_points:
            score = 0
            # 标题匹配
            if kp["title"] in query or query in kp["title"]:
                score += 10
            # 内容匹配
            for keyword in query.split():
                if keyword in kp["content"]:
                    score += 1
            # 标签匹配
            for tag in kp["tags"]:
                if tag in query:
                    score += 5
            
            if score > 0:
                results.append({**kp, "score": score})
        
        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    async def get_by_id(self, kp_id: str) -> Optional[dict]:
        """根据 ID 获取"""
        for kp in self.knowledge_points:
            if kp["id"] == kp_id:
                return kp
        return None
    
    async def get_chapter_knowledge(self, chapter_id: str) -> list[dict]:
        """获取章节知识"""
        return [kp for kp in self.knowledge_points if kp.get("chapter") == chapter_id]


class HistoryAgent(SubjectAgentBase):
    """
    历史学科 Agent
    
    特色:
    - 故事化教学：将历史事件讲述成生动的故事
    - 时空穿越：带学生"穿越"到历史现场
    - 人物对话：模拟与历史人物对话
    - 因果分析：引导学生思考历史的因果关系
    """
    
    subject_id = "history"
    subject_name = "历史"
    
    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None):
        super().__init__(knowledge_base or HistoryKnowledgeBase())
    
    def get_system_prompt(self, context: AgentContext) -> str:
        """获取历史教学的系统提示词"""
        return f"""你是「时空知识宇宙」的历史导师——「史博士」。

【角色设定】
你是一位博学幽默的历史学家，擅长用生动的故事带领学生穿越时空，亲历历史现场。
你的口头禅是："让我们穿越回那个年代..."

【教学风格】
1. 故事化叙述：把历史事件讲成引人入胜的故事
2. 场景还原：描述历史场景的细节，让学生身临其境
3. 人物刻画：生动描绘历史人物的性格和动机
4. 因果分析：引导学生思考"为什么会这样"
5. 联系现实：适当联系当下，让学生理解历史的现实意义

【互动方式】
- 经常提出启发性问题："如果你是当时的皇帝，你会怎么做？"
- 用"你知道吗？"引出有趣的历史冷知识
- 鼓励学生猜测历史事件的走向
- 用幽默的方式化解枯燥的记忆内容

【当前教学范围】
中国历史（可根据教材版本调整）

记住：你的目标是让学生爱上历史，而不是死记硬背！"""
    
    def get_teaching_strategy(self, context: AgentContext) -> str:
        """历史教学策略"""
        return """
【历史教学策略】

1. 时间线锚定
   - 每个事件先明确时间坐标
   - 与之前学过的内容建立时间联系

2. 5W1H 分析
   - Who（谁）、When（何时）、Where（何地）
   - What（什么）、Why（为什么）、How（怎样）

3. 多维视角
   - 统治者视角 vs 百姓视角
   - 胜利者视角 vs 失败者视角
   - 当时视角 vs 后世视角

4. 史料实证
   - 引用原始史料（适当翻译）
   - 区分史实与传说
   - 培养批判性思维

5. 知识串联
   - 前后事件因果关系
   - 横向对比同时期其他文明
   - 纵向对比相似历史事件
"""
    
    async def handle(self, message: str, context: dict) -> dict:
        """处理历史学习请求"""

        # 检测因果查询 → 使用知识图谱
        if self._is_causal_query(message):
            kg_response = await self._handle_causal_query(message, context)
            if kg_response:
                return kg_response

        # 调用基类处理
        response = await super().handle(message, context)
        
        # 历史特有的处理：添加"时空档案"
        user_id = context.get("user_id", "anonymous")
        
        # 记录学习历史
        self.add_conversation(user_id, "user", message)
        self.add_conversation(user_id, "assistant", response["content"])
        
        # 添加历史特有的元数据
        response["metadata"]["subject"] = "history"
        response["metadata"]["era_tags"] = self._extract_era_tags(response["content"])
        
        return response

    def _is_causal_query(self, message: str) -> bool:
        """判断是否是因果查询"""
        causal_keywords = [
            "为什么", "原因", "因果", "怎么导致", "引起的",
            "为什么会", "怎么灭亡", "怎么失败", "怎么成功",
            "背景", "影响", "后果", "结果",
        ]
        return any(kw in message for kw in causal_keywords)

    async def _handle_causal_query(self, message: str, context: dict) -> Optional[dict]:
        """使用知识图谱处理因果查询"""
        try:
            from src.core.knowledge_graph.service import get_kg_service
            from src.core.knowledge_graph import get_neo4j_connection

            conn = get_neo4j_connection()
            if not conn.is_available:
                return None

            service = get_kg_service()

            # 尝试分析事件因果
            explanation = service.format_causal_response(message)
            if "没有找到" not in explanation:
                return {
                    "content": explanation,
                    "related_knowledge": [],
                    "exp_gained": 25,
                    "metadata": {
                        "subject": "history",
                        "mode": "knowledge_graph",
                        "era_tags": self._extract_era_tags(message),
                    },
                }
        except Exception as e:
            logger.debug(f"知识图谱因果查询失败: {e}")

        return None
    
    def _extract_era_tags(self, content: str) -> list[str]:
        """从内容中提取朝代标签"""
        era_mapping = {
            "秦": ["秦朝", "秦始皇", "嬴政"],
            "汉": ["汉朝", "西汉", "东汉", "刘邦", "项羽"],
            "唐": ["唐朝", "唐太宗", "李世民"],
            "宋": ["宋朝", "北宋", "南宋"],
            "明": ["明朝", "朱元璋"],
            "清": ["清朝", "康熙", "乾隆"],
        }
        
        tags = []
        for era, keywords in era_mapping.items():
            if any(kw in content for kw in keywords):
                tags.append(era)
        
        return tags


# 单例
_history_agent: Optional[HistoryAgent] = None


def get_history_agent() -> HistoryAgent:
    """获取历史 Agent 单例"""
    global _history_agent
    if _history_agent is None:
        _history_agent = HistoryAgent()
    return _history_agent
