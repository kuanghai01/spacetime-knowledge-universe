"""
数学科 Agent

特色:
- 可视化推理: 数轴、坐标系、几何图形的直观演示
- 互动解题: 一步步引导，遇到易错点主动提醒
- 公式推导: 展示公式背后的逻辑，而非死记硬背
- 分层练习: 基础→提高→挑战，根据水平动态调整

数学知识库覆盖数与代数、图形与几何、统计与概率、函数等初中核心领域。
"""
import logging
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

from src.agents.base_agent import SubjectAgentBase, KnowledgeBase, AgentContext
from src.data.math_data import ALL_MATH_KNOWLEDGE, ALL_MATH_VISUALIZATIONS

logger = logging.getLogger(__name__)


class MathDomain(str, Enum):
    """数学分支"""
    NUMBER = "数与代数"
    GEOMETRY = "图形与几何"
    STATISTICS = "统计与概率"
    FUNCTION = "函数"


@dataclass
class Visualization:
    """可视化描述"""
    id: str
    title: str
    domain: MathDomain
    description: str
    steps: list[str]
    conclusion: str = ""
    related_knowledge: list[str] = field(default_factory=list)
    difficulty: int = 1


class MathKnowledgeBase(KnowledgeBase):
    """数学知识库——加载初中完整数学课程（120+个知识点）"""

    def __init__(self):
        # 从数据模块加载完整知识库
        self.knowledge_points = [kp.copy() for kp in ALL_MATH_KNOWLEDGE]

        # 从数据模块加载可视化演示
        self.visualizations: list[Visualization] = []
        for vis in ALL_MATH_VISUALIZATIONS:
            vis_copy = vis.copy()
            domain_str = vis_copy.get("domain", "数与代数")
            # 将字符串domain转换为MathDomain枚举
            domain_enum = MathDomain.NUMBER
            for md in MathDomain:
                if md.value == domain_str:
                    domain_enum = md
                    break
            vis_copy["domain"] = domain_enum
            self.visualizations.append(Visualization(**vis_copy))

    async def search(self, query: str, limit: int = 5) -> list[dict]:
        """搜索数学知识点"""
        results = []
        query_lower = query.lower()

        for kp in self.knowledge_points:
            score = 0
            keywords = kp.get("keywords", kp.get("tags", []))
            if any(kw in query_lower for kw in keywords):
                score += 3
            if any(kw in kp.get("title", "") for kw in query_lower.split()):
                score += 2
            if kp.get("title", "") in query_lower:
                score += 5

            if score > 0:
                results.append({**kp, "score": score})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    async def get_by_id(self, kp_id: str) -> Optional[dict]:
        """根据ID获取知识点"""
        for kp in self.knowledge_points:
            if kp["id"] == kp_id:
                return kp
        return None

    async def get_chapter_knowledge(self, chapter: str) -> list[dict]:
        """获取章节知识点"""
        chapter_mapping = {
            "数与代数": [kp for kp in self.knowledge_points if kp.get("domain") in ["数与代数"]],
            "图形与几何": [kp for kp in self.knowledge_points if kp.get("domain") == "图形与几何"],
            "统计与概率": [kp for kp in self.knowledge_points if kp.get("domain") == "统计与概率"],
            "函数": [kp for kp in self.knowledge_points if kp.get("domain") == "函数"],
        }

        for key, kps in chapter_mapping.items():
            if key in chapter and kps:
                return kps

        # 尝试匹配chapter字段
        for kp in self.knowledge_points:
            if kp.get("chapter", "") == chapter:
                return [kp]

        return self.knowledge_points[:5]

    def get_visualizations_by_knowledge(self, kp_ids: list[str]) -> list[Visualization]:
        """根据知识点获取可视化演示"""
        results = []
        for vis in self.visualizations:
            if any(kp_id in vis.related_knowledge for kp_id in kp_ids):
                results.append(vis)
        return results

    def get_visualizations_by_domain(self, domain: MathDomain) -> list[Visualization]:
        """根据数学分支获取可视化演示"""
        return [vis for vis in self.visualizations if vis.domain == domain]


class MathAgent(SubjectAgentBase):
    """数学 Agent - 数先生"""

    def __init__(self):
        super().__init__()
        self.knowledge_base = MathKnowledgeBase()
        self._subject_id = "math"
        self._subject_name = "数学"

    @property
    def subject_id(self) -> str:
        return self._subject_id

    @property
    def subject_name(self) -> str:
        return self._subject_name

    def get_system_prompt(self, context: AgentContext) -> str:
        return (
            f"你是「时空知识宇宙」的数学导师「数先生」。\n"
            f"你擅长用直观的可视化方式讲解抽象的数学概念。\n"
            f"你的教学风格：数形结合，从具体到抽象，让学生不仅知其然，更知其所以然。\n\n"
            f"## 当前学生信息\n"
            f"用户ID: {context.user_id}\n"
            f"学习水平: {context.user_level}\n\n"
            f"## 教学规则\n"
            f"1. 讲解新概念时，先给出具体的数字例子，再归纳一般规律\n"
            f"2. 解题时展示完整步骤，并解释每一步的依据\n"
            f"3. 遇到易错点主动提醒（如去括号变号、移项变号）\n"
            f"4. 鼓励学生用不同方法解题，培养发散思维\n"
            f"5. 适时使用数轴、坐标系、几何图形来辅助理解\n\n"
            f"请用简洁、清晰的语言回应，使用Markdown格式。"
        )

    def _is_visualization_request(self, message: str) -> bool:
        """判断是否需要视觉演示"""
        keywords = ["画图", "图像", "数轴", "坐标系", "演示", "展示", "可视", "图示", "画", "图"]
        return any(kw in message for kw in keywords)

    def _is_problem_solving(self, message: str) -> bool:
        """判断是否是解题请求"""
        keywords = ["解", "计算", "怎么做", "过程", "步骤", "等于多少", "求解"]
        return any(kw in message for kw in keywords)

    def _format_visualization(self, vis: Visualization, context: AgentContext) -> str:
        """格式化可视化演示"""
        lines = [
            f"📐 **{vis.title}**",
            "",
            f"*{vis.description}*",
            "",
            "**演示步骤：**",
        ]

        for i, step in enumerate(vis.steps, 1):
            lines.append(f"{i}. {step}")

        conclusion = vis.conclusion or vis.description
        lines.extend([
            "",
            f"✅ **结论：** {conclusion}",
            "",
            "---",
            "*来自时空知识宇宙·数学可视化实验室* 📊",
        ])

        return "\n".join(lines)

    def _extract_domain_tags(self, message: str) -> list[str]:
        """提取数学分支标签"""
        tags = []
        domain_keywords = {
            "数与代数": ["有理数", "整式", "方程", "不等式", "实数", "二次根式", "代数"],
            "图形与几何": ["角", "线", "三角形", "圆", "平行", "垂直", "面积", "体积", "几何", "四边形", "勾股"],
            "统计与概率": ["数据", "平均", "中位数", "众数", "普查", "样本", "概率", "统计"],
            "函数": ["函数", "图像", "直线", "抛物线", "斜率", "正比例", "反比例", "一次函数", "二次函数"],
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in message for kw in keywords):
                tags.append(domain)

        return tags

    def _suggest_visualizations(self, message: str) -> list[Visualization]:
        """推荐可视化演示"""
        domain_mapping = {
            "数与代数": MathDomain.NUMBER,
            "图形与几何": MathDomain.GEOMETRY,
            "统计与概率": MathDomain.STATISTICS,
            "函数": MathDomain.FUNCTION,
        }

        tags = self._extract_domain_tags(message)
        results = []

        for tag in tags:
            if tag in domain_mapping:
                results.extend(
                    self.knowledge_base.get_visualizations_by_domain(
                        domain_mapping[tag]
                    )
                )

        return results[:2]

    async def handle(self, message: str, context: dict) -> dict:
        """处理用户消息"""

        # 1. 搜索相关知识
        kb_results = await self.knowledge_base.search(message)

        # 2. 检查是否需要可视化演示
        if self._is_visualization_request(message):
            suggestions = self._suggest_visualizations(message)
            if suggestions:
                viz_content = self._format_visualization(suggestions[0], AgentContext(
                    user_id=context.get("user_id", "anonymous")
                ))
                return {
                    "content": viz_content,
                    "related_knowledge": [
                        {"title": kp.get("title", "")}
                        for kp in kb_results[:3]
                    ],
                    "exp_gained": 20,
                    "metadata": {
                        "subject": "math",
                        "viz_id": suggestions[0].id,
                        "mode": "visualization",
                    },
                }
            # 无可匹配的可视化 → 返回可视化引导提示
            return {
                "content": "📐 **数学可视化实验室**\n\n数先生可以用图形帮你理解数学概念！目前支持的可视化：\n\n- 📏 **数轴上的有理数** — 直观感受正负数大小\n- ⚖️ **解方程——天平原理** — 理解等式性质\n- 📈 **一次函数图像绘制** — 观察斜率的作用\n- 📊 **二次函数——抛物线** — 探索抛物线特点\n- 🔺 **三角形内角和验证** — 验证内角和 = 180°\n- 📐 **勾股定理证明** — 面积法证明 a²+b²=c²\n- 📊 **数据可视化——扇形统计图** — 绘制统计图\n\n试试说\"演示三角形内角和\"或\"画一次函数的图像\"！",
                "related_knowledge": [
                    {"title": kp.get("title", "")}
                    for kp in kb_results[:3]
                ],
                "exp_gained": 10,
                "metadata": {
                    "subject": "math",
                    "mode": "visualization_menu",
                },
            }

        # 3. 检查是否是解题请求 → 基类处理+建议任务
        if self._is_problem_solving(message) and kb_results:
            response = await super().handle(message, context)
            response["suggested_task"] = {
                "type": "practice",
                "title": f"练习：{kb_results[0]['title']}",
                "description": f"完成关于「{kb_results[0]['title']}」的3道练习题",
                "exp_reward": 50,
            }
            response["metadata"]["mode"] = "problem_solving"
            return response

        # 4. 默认处理
        return await super().handle(message, context)


def get_math_agent() -> MathAgent:
    """获取数学 Agent 实例"""
    return MathAgent()
