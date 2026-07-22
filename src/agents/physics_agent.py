"""
物理学科 Agent

特色:
- 虚拟实验室: 通过交互式互动演示物理现象
- 现象探究: 从生活现象出发，引导学生探索原理
- 公式推导演示: 一步步展示物理公式的推导过程
- 实验设计: 引导学生设计简单的物理实验

物理知识库覆盖了经典力学、热学、光学、电学等基础领域。
"""
import logging
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

from src.agents.base_agent import SubjectAgentBase, KnowledgeBase, AgentContext
from src.data.physics_data import ALL_PHYSICS_KNOWLEDGE, ALL_PHYSICS_EXPERIMENTS, PhysicsDomain as DataPhysicsDomain

logger = logging.getLogger(__name__)


class PhysicsDomain(str, Enum):
    """物理学分支（与数据模块保持一致）"""
    MECHANICS = "力学"
    THERMODYNAMICS = "热学"
    OPTICS = "光学"
    ELECTRICITY = "电学"
    ACOUSTICS = "声学"
    MODERN = "现代物理"

    @classmethod
    def from_string(cls, value: str) -> 'PhysicsDomain':
        """从字符串获取枚举，兼容数据模块的域名称"""
        for member in cls:
            if member.value == value:
                return member
        return cls.MECHANICS


@dataclass
class VirtualExperiment:
    """虚拟实验"""
    id: str
    title: str
    domain: PhysicsDomain
    description: str
    principle: str
    steps: list[str]
    observations: list[str]
    related_knowledge: list[str]
    difficulty: int = 1


class PhysicsKnowledgeBase(KnowledgeBase):
    """物理知识库"""
    
    def __init__(self):
        # 从数据模块加载完整物理知识库（84个知识点）
        self.knowledge_points = []
        for kp in ALL_PHYSICS_KNOWLEDGE:
            kp_copy = kp.copy()
            # 将字符串domain转换为PhysicsDomain枚举
            domain_str = kp_copy.get("domain", "力学")
            kp_copy["domain"] = PhysicsDomain.from_string(domain_str)
            self.knowledge_points.append(kp_copy)

        # 从数据模块加载虚拟实验
        self.experiments = []
        for exp in ALL_PHYSICS_EXPERIMENTS:
            exp_copy = exp.copy()
            domain_str = exp_copy.get("domain", "力学")
            exp_copy["domain"] = PhysicsDomain.from_string(domain_str)
            self.experiments.append(VirtualExperiment(**exp_copy))
    
    async def search(self, query: str, limit: int = 5) -> list[dict]:
        """搜索知识点（结合关键词和物理领域）"""
        import re
        
        query_lower = query.lower()
        results = []
        
        # 领域关键词映射
        domain_keywords = {
            PhysicsDomain.MECHANICS: ["力", "运动", "速度", "加速度", "牛顿", "惯性"],
            PhysicsDomain.OPTICS: ["光", "反射", "折射", "影子", "透镜", "镜子"],
            PhysicsDomain.ELECTRICITY: ["电", "电路", "电压", "电阻", "电流", "欧姆"],
            PhysicsDomain.THERMODYNAMICS: ["热", "温度", "热量", "比热"],
            PhysicsDomain.ACOUSTICS: ["声", "音", "振动", "波动"],
        }
        
        detected_domains = set()
        for domain, keywords in domain_keywords.items():
            if any(kw in query_lower for kw in keywords):
                detected_domains.add(domain)
        
        for kp in self.knowledge_points:
            score = 0
            
            # 标题匹配
            if kp["title"] in query or query in kp["title"]:
                score += 10
            
            # 关键词匹配
            for keyword in re.split(r'[\s,，、]+', query_lower):
                if keyword in kp["content"]:
                    score += 2
                if any(keyword == tag for tag in kp["tags"]):
                    score += 5
            
            # 领域匹配（如果检测到领域）
            if detected_domains and kp["domain"] in detected_domains:
                score += 3
            
            if score > 0:
                results.append({**kp, "score": score})
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    async def get_by_id(self, kp_id: str) -> Optional[dict]:
        """根据 ID 获取知识点"""
        for kp in self.knowledge_points:
            if kp["id"] == kp_id:
                return kp
        return None
    
    async def get_chapter_knowledge(self, chapter_id: str) -> list[dict]:
        """获取章节知识点"""
        return [kp for kp in self.knowledge_points if kp.get("chapter") == chapter_id]
    
    def get_experiments_by_knowledge(self, kp_ids: list[str]) -> list[VirtualExperiment]:
        """获取与知识点相关的虚拟实验"""
        results = []
        for exp in self.experiments:
            if any(kp_id in exp.related_knowledge for kp_id in kp_ids):
                results.append(exp)
        return results
    
    def get_experiments_by_domain(self, domain: PhysicsDomain) -> list[VirtualExperiment]:
        """获取某个物理分支的虚拟实验"""
        return [exp for exp in self.experiments if exp.domain == domain]


class PhysicsAgent(SubjectAgentBase):
    """
    物理学科 Agent
    
    特色:
    - 虚拟实验室: 交互式实验演示
    - 现象探究: 从生活现象出发
    - 公式推理: 逐步展示公式推导
    - 实验设计: 引导学生自主设计实验
    
    教学风格: "让我们通过实验来发现..."
    """
    
    subject_id = "physics"
    subject_name = "物理"
    
    def __init__(self, knowledge_base: Optional[PhysicsKnowledgeBase] = None):
        super().__init__(knowledge_base or PhysicsKnowledgeBase())
    
    def get_system_prompt(self, context: AgentContext) -> str:
        return f"""你是「时空知识宇宙」的物理导师——「物先生」。

【角色设定】
你是一位充满好奇心的物理老师，擅长用实验和生活中的现象来解释物理原理。
你的口头禅是："让我们通过实验来发现..."

【教学风格】
1. 现象引入：从日常生活中的有趣现象出发
2. 实验探究：通过虚拟实验让学生"亲眼看到"物理过程
3. 原理总结：用简单的语言归纳物理定律
4. 公式推导：一步步展示公式的来源和推导
5. 应用拓展：介绍物理知识在现代科技中的应用

【互动方式】
- "你想知道为什么吗？让我们做个实验..."
- "观察到了什么现象？你有什么猜想？"
- 用虚拟实验室工具演示难以实物操作的实验
- 鼓励学生在家用简单材料做物理实验

【当前教学范围】
初中物理（力学、光学、热学、电学基础）

记住：物理不是做题，而是理解这个世界的运行规律！"""
    
    def get_teaching_strategy(self, context: AgentContext) -> str:
        return """
【物理教学策略】

1. 情境引入（3-5分钟）
   - 用一个有趣的现象或问题引入
   - 让学生先思考、猜测
   - 激发求知欲

2. 实验探究（5-10分钟）
   - 演示虚拟实验
   - 引导学生观察关键现象
   - 记录实验数据
   - 得出初步结论

3. 原理讲解（5-8分钟）
   - 从实验现象归纳物理规律
   - 推导公式（展示每一步的来源）
   - 强调物理量的物理意义

4. 应用迁移（3-5分钟）
   - 解释生活中的相关现象
   - 介绍现代科技应用
   - 提出拓展思考问题

5. 实验设计挑战
   - 鼓励学生设计验证性实验
   - 用家里材料做简单实验
   - 培养科学探究能力
"""
    
    async def handle(self, message: str, context: dict) -> dict:
        """处理物理学习请求"""
        import re
        
        # 检查是否请求虚拟实验
        if self._is_experiment_request(message):
            response = await self._handle_experiment_request(message, context)
        else:
            # 调用基类处理
            response = await super().handle(message, context)
            
            # 添加到相关虚拟实验的建议
            related_experiments = self._suggest_experiments(message)
            if related_experiments:
                response["related_experiments"] = related_experiments
        
        response["metadata"]["subject"] = "physics"
        response["metadata"]["domain_tags"] = self._extract_domain_tags(message)
        
        return response
    
    def _is_experiment_request(self, message: str) -> bool:
        """判断是否请求虚拟实验"""
        experiment_keywords = ["实验", "演示", "观察", "做一做", "验证", "探究"]
        return any(kw in message for kw in experiment_keywords)
    
    async def _handle_experiment_request(self, message: str, context: dict) -> dict:
        """处理虚拟实验请求"""
        # 搜索相关实验
        related_knowledge = []
        if self.knowledge_base:
            related_knowledge = await self.knowledge_base.search(
                query=message,
                limit=3
            )
        
        # 查找相关虚拟实验
        kp_ids = [kp.get("id") for kp in related_knowledge if kp.get("id")]
        experiments = self.knowledge_base.get_experiments_by_knowledge(kp_ids) if self.knowledge_base else []
        
        # 如果没有找到，根据消息内容猜测领域
        if not experiments and self.knowledge_base:
            domain_keywords = {
                PhysicsDomain.OPTICS: ["光", "反射", "折射", "影子"],
                PhysicsDomain.MECHANICS: ["力", "运动", "速度", "惯性"],
                PhysicsDomain.ELECTRICITY: ["电", "电路", "电流", "电压"],
            }
            for domain, keywords in domain_keywords.items():
                if any(kw in message for kw in keywords):
                    experiments = self.knowledge_base.get_experiments_by_domain(domain)
                    break
        
        if experiments:
            exp = experiments[0]
            content = self._format_experiment(exp, context)
            return {
                "content": content,
                "related_knowledge": related_knowledge,
                "related_experiments": [exp],
                "suggested_task": {
                    "type": "virtual_experiment",
                    "title": f"完成实验: {exp.title}",
                    "experiment_id": exp.id,
                },
                "exp_gained": 20,
                "metadata": {
                    "subject": "physics",
                    "experiment_id": exp.id,
                    "mode": "virtual_lab",
                }
            }
        
        # 没有找到相关实验，返回普通回答
        return await super().handle(message, context)
    
    def _format_experiment(self, exp: VirtualExperiment, context: dict) -> str:
        """格式化虚拟实验内容"""
        steps_text = "\n".join(f"  {i+1}. {step}" for i, step in enumerate(exp.steps))
        observations_text = "\n".join(f"  • {obs}" for obs in exp.observations)
        
        return f"""🧪 **虚拟实验室: {exp.title}**

📝 **实验目的**
{exp.description}

🔬 **实验原理**
{exp.principle}

📋 **实验步骤**
{steps_text}

👀 **观察与记录**
{observations_text}

💡 **实验结论**
{exp.principle}

🎯 **小挑战**
你能用身边的物品设计一个类似的小实验吗？试试用家里的材料重复这个实验！

---
*来自时空知识宇宙·虚拟实验室*"""
    
    def _suggest_experiments(self, message: str) -> list[dict]:
        """建议相关虚拟实验"""
        if not self.knowledge_base:
            return []
        
        results = []
        for exp in self.knowledge_base.experiments:
            # 简单匹配：实验标题或知识点是否在消息中出现
            if any(kw in message for kw in exp.title.split()):
                results.append({
                    "id": exp.id,
                    "title": exp.title,
                    "domain": exp.domain.value,
                    "difficulty": exp.difficulty,
                })
        return results[:3]  # 最多返回3个
    
    def _extract_domain_tags(self, message: str) -> list[str]:
        """提取物理领域标签"""
        domain_keywords = {
            "力学": ["力", "运动", "速度", "加速度", "牛顿", "惯性", "重力"],
            "光学": ["光", "反射", "折射", "影子", "透镜", "镜子", "颜色"],
            "热学": ["热", "温度", "热量", "比热", "熔化", "沸腾"],
            "电学": ["电", "电路", "电压", "电阻", "电流", "电源"],
            "声学": ["声", "音", "振动", "频率"],
        }
        
        tags = []
        for domain, keywords in domain_keywords.items():
            if any(kw in message for kw in keywords):
                tags.append(domain)
        return tags


# 单例
_physics_agent: Optional[PhysicsAgent] = None


def get_physics_agent() -> PhysicsAgent:
    """获取物理 Agent 单例"""
    global _physics_agent
    if _physics_agent is None:
        _physics_agent = PhysicsAgent()
    return _physics_agent
