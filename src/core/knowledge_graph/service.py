"""
知识图谱 - 服务层

提供高级查询服务，供 Agent 调用:
1. 因果分析 - 为什么发生？导致了什么？
2. 人物画像 - 人物的事件网络和关系网络
3. 朝代概览 - 朝代的关键事件和人物
4. 学习路径 - 知识点的依赖链
5. 跨学科桥梁 - 连接不同学科的知识
"""
import logging
from typing import Optional

from src.core.knowledge_graph.repository import (
    get_kg_repository,
    KnowledgeGraphRepository,
)

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """知识图谱服务层"""

    def __init__(self):
        self.repo = get_kg_repository()

    def analyze_event(self, event_name: str) -> Optional[dict]:
        """
        分析历史事件（因果链+参与者+相关知识）

        Args:
            event_name: 事件名称（模糊匹配）

        Returns:
            事件分析结果，包含因果链、参与者、知识点
        """
        # 搜索匹配的事件
        nodes = self.repo.search_nodes(event_name, limit=5)
        if not nodes:
            return None

        # 找到第一个事件节点
        event_node = None
        for node in nodes:
            if "HistoricalEvent" in node.get("_labels", []):
                event_node = node
                break

        if not event_node:
            return None

        event_id = event_node["id"]
        network = self.repo.get_full_causal_network(event_id, depth=2)

        return {
            "event": {
                "name": event_node.get("name", ""),
                "description": event_node.get("description", ""),
                "year": event_node.get("start_year", ""),
                "dynasty": event_node.get("dynasty", ""),
                "location": event_node.get("location", ""),
            },
            "causes": [
                {"name": c.get("name", ""), "depth": c.get("depth", 0)}
                for c in network.get("causes", [])
                if c.get("name")
            ],
            "consequences": [
                {"name": c.get("name", ""), "depth": c.get("depth", 0)}
                for c in network.get("consequences", [])
                if c.get("name")
            ],
            "participants": [
                {"name": p.get("name", ""), "role": p.get("role", "")}
                for p in network.get("participants", [])
            ],
            "related_knowledge": [
                {"title": kp.get("title", ""), "content": kp.get("content", "")}
                for kp in network.get("related_knowledge", [])
            ],
        }

    def analyze_person(self, person_name: str) -> Optional[dict]:
        """
        分析历史人物（参与事件+人物关系+朝代）

        Args:
            person_name: 人物名称

        Returns:
            人物分析结果
        """
        nodes = self.repo.search_nodes(person_name, limit=5)
        if not nodes:
            return None

        person_node = None
        for node in nodes:
            if "Person" in node.get("_labels", []):
                person_node = node
                break

        if not person_node:
            return None

        person_id = person_node["id"]
        network = self.repo.get_person_network(person_id)

        return {
            "person": {
                "name": person_node.get("name", ""),
                "dynasty": person_node.get("dynasty", ""),
                "title": person_node.get("title", ""),
                "description": person_node.get("description", ""),
            },
            "events": [
                {
                    "name": e.get("name", ""),
                    "year": e.get("start_year", ""),
                    "role": e.get("role", ""),
                }
                for e in network.get("events", [])
            ],
            "relationships": [
                {
                    "person": r.get("person", {}).get("name", ""),
                    "type": r.get("type", ""),
                }
                for r in network.get("relationships", [])
            ],
            "dynasty": (
                {
                    "name": network["dynasty"].get("name", ""),
                    "period": f"{network['dynasty'].get('start_year', '')} - {network['dynasty'].get('end_year', '')}",
                }
                if network.get("dynasty")
                else None
            ),
        }

    def get_causal_explanation(self, event_name: str) -> Optional[str]:
        """
        生成事件的因果解释（自然语言）

        例如：为什么秦能统一六国？
        """
        analysis = self.analyze_event(event_name)
        if not analysis:
            return None

        event = analysis["event"]
        lines = []

        # 事件基本信息
        year_str = f"（{event['year']}年）" if event.get("year") else ""
        lines.append(f"## 📖 {event['name']}{year_str}")
        lines.append(f"\n{event.get('description', '')}\n")

        # 前因
        causes = analysis.get("causes", [])
        if causes:
            lines.append("### 🔙 前因（为什么发生？）")
            # 按深度去重，取直接原因（depth=1）
            direct_causes = [c for c in causes if c.get("depth") == 1]
            for cause in direct_causes[:3]:
                lines.append(f"- **{cause['name']}**")

            deeper_causes = [c for c in causes if c.get("depth", 0) > 1]
            if deeper_causes:
                lines.append(f"- *更深层原因: {', '.join(c['name'] for c in deeper_causes[:2])}*")
            lines.append("")

        # 后果
        consequences = analysis.get("consequences", [])
        if consequences:
            lines.append("### 🔜 后果（导致了什么？）")
            direct_consequences = [c for c in consequences if c.get("depth") == 1]
            for cons in direct_consequences[:3]:
                lines.append(f"- **{cons['name']}**")
            lines.append("")

        # 参与者
        participants = analysis.get("participants", [])
        if participants:
            lines.append("### 👥 关键人物")
            for p in participants:
                role_str = f"（{p['role']}）" if p.get("role") else ""
                lines.append(f"- **{p['name']}**{role_str}")
            lines.append("")

        # 相关知识
        knowledge = analysis.get("related_knowledge", [])
        if knowledge:
            lines.append("### 📝 相关知识点")
            for kp in knowledge[:3]:
                lines.append(f"- **{kp['title']}**: {kp.get('content', '')}")
            lines.append("")

        return "\n".join(lines)

    def get_timeline(self, dynasty_name: str) -> Optional[dict]:
        """获取朝代时间线"""
        events = self.repo.get_dynasty_events(dynasty_name)
        persons = self.repo.get_dynasty_persons(dynasty_name)

        if not events and not persons:
            return None

        return {
            "dynasty": dynasty_name,
            "events": [
                {
                    "name": e.get("name", ""),
                    "year": e.get("start_year", ""),
                    "importance": e.get("importance", 1),
                    "description": e.get("description", ""),
                }
                for e in events
            ],
            "notable_persons": [
                {"name": p.get("name", ""), "title": p.get("title", "")}
                for p in persons
            ],
        }

    def get_graph_statistics(self) -> dict:
        """获取图谱统计"""
        return {
            "nodes": self.repo.count_nodes(),
            "relationships": self.repo.count_relationships(),
        }

    def format_causal_response(self, event_name: str) -> str:
        """
        格式化因果分析响应（供前端展示）
        """
        analysis = self.analyze_event(event_name)
        if not analysis:
            return f"抱歉，我没有找到关于「{event_name}」的知识图谱信息。"

        event = analysis["event"]

        # 构建知识图谱卡片
        lines = [
            f"## 🕸️ 知识图谱：{event['name']}",
            f"*{event.get('description', '')}*",
            "",
        ]

        # 因果链可视化
        causes = [c["name"] for c in analysis.get("causes", []) if c.get("depth") == 1]
        event_str = event["name"]
        consequences = [c["name"] for c in analysis.get("consequences", []) if c.get("depth") == 1]

        if causes or consequences:
            lines.append("### 因果链")
            chain_parts = []
            if causes:
                chain_parts.append(" → ".join(causes[:3]))
            chain_parts.append(f"**{event_str}**")
            if consequences:
                chain_parts.append(" → ".join(consequences[:3]))
            lines.append(" → ".join(chain_parts))
            lines.append("")

        # 关键人物
        participants = analysis.get("participants", [])
        if participants:
            lines.append("### 关键人物")
            for p in participants[:4]:
                role_str = f"（{p['role']}）" if p.get("role") else ""
                lines.append(f"- **{p['name']}**{role_str}")
            lines.append("")

        # 相关知识
        knowledge = analysis.get("related_knowledge", [])
        if knowledge:
            lines.append("### 相关知识点")
            for kp in knowledge[:3]:
                lines.append(f"- **{kp['title']}**")
            lines.append("")

        lines.append("---")
        lines.append("*来自时空知识宇宙·知识图谱* 🕸️")

        return "\n".join(lines)


def get_kg_service() -> KnowledgeGraphService:
    """获取知识图谱服务实例"""
    return KnowledgeGraphService()
