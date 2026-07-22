"""
知识图谱 - 数据访问层

提供 CRUD 操作和复杂查询:
1. 节点创建/更新/删除
2. 关系创建/删除
3. 路径查询（因果链、人物关系）
4. 子图查询（围绕事件的关联网络）
"""
import logging
from typing import Optional

from src.core.knowledge_graph import get_neo4j_connection
from src.core.knowledge_graph.models import (
    GraphNode,
    GraphRelationship,
    Subject,
    HistoricalEvent,
    Person,
    Dynasty,
    KnowledgePoint,
    Location,
    NodeType,
    RelationshipType,
)

logger = logging.getLogger(__name__)


class KnowledgeGraphRepository:
    """知识图谱数据访问层"""

    def __init__(self):
        self.conn = get_neo4j_connection()

    def _run_query(self, query: str, parameters: dict = None):
        """执行 Cypher 查询"""
        if not self.conn.is_available:
            logger.warning("⚠️ Neo4j 不可用，查询跳过")
            return None

        try:
            with self.conn.session() as session:
                result = session.run(query, parameters or {})
                return list(result)
        except Exception as e:
            logger.error(f"Neo4j 查询失败: {e}")
            return None

    # =========================================================
    # 节点 CRUD
    # =========================================================

    def create_node(self, node: GraphNode) -> bool:
        """创建节点（MERGE，避免重复）"""
        props = {k: v for k, v in node.properties.items()}
        props_str = ", ".join(f"{k}: ${k}" for k in props.keys())

        query = (
            f"MERGE (n:{node.label.value} {{id: $id}}) "
            f"SET n += {{{props_str}}} "
            f"RETURN n"
        )
        params = {"id": node.id, **props}

        result = self._run_query(query, params)
        return result is not None and len(result) > 0

    def create_subject(self, subject: Subject) -> bool:
        return self.create_node(subject.to_node())

    def create_event(self, event: HistoricalEvent) -> bool:
        return self.create_node(event.to_node())

    def create_person(self, person: Person) -> bool:
        return self.create_node(person.to_node())

    def create_dynasty(self, dynasty: Dynasty) -> bool:
        return self.create_node(dynasty.to_node())

    def create_knowledge_point(self, kp: KnowledgePoint) -> bool:
        return self.create_node(kp.to_node())

    def create_location(self, location: Location) -> bool:
        return self.create_node(location.to_node())

    def get_node_by_id(self, node_id: str) -> Optional[dict]:
        """根据ID获取节点"""
        query = "MATCH (n {id: $id}) RETURN n, labels(n) AS labels"
        result = self._run_query(query, {"id": node_id})
        if result:
            record = result[0]
            node = dict(record["n"])
            node["_labels"] = record["labels"]
            return node
        return None

    # =========================================================
    # 关系 CRUD
    # =========================================================

    def create_relationship(self, rel: GraphRelationship) -> bool:
        """创建关系"""
        props = {k: v for k, v in rel.properties.items()}
        props_str = ", ".join(f"{k}: ${k}" for k in props.keys())

        query = (
            f"MATCH (a {{id: $source}}), (b {{id: $target}}) "
            f"MERGE (a)-[r:{rel.rel_type.value}]->(b) "
        )
        if props_str:
            query += f"SET r += {{{props_str}}} "
        query += "RETURN r"

        params = {"source": rel.source_id, "target": rel.target_id, **props}
        result = self._run_query(query, params)
        return result is not None and len(result) > 0

    # =========================================================
    # 批量创建
    # =========================================================

    def batch_create(self, nodes: list[GraphNode], rels: list[GraphRelationship]) -> bool:
        """批量创建节点和关系（单事务）"""
        if not self.conn.is_available:
            return False

        try:
            with self.conn.session() as session:
                with session.begin_transaction() as tx:
                    # 批量创建节点
                    for node in nodes:
                        props = {k: v for k, v in node.properties.items()}
                        props_str = ", ".join(f"{k}: ${k}" for k in props.keys())
                        query = (
                            f"MERGE (n:{node.label.value} {{id: $id}}) "
                            f"SET n += {{{props_str}}}"
                        )
                        tx.run(query, {"id": node.id, **props})

                    # 批量创建关系
                    for rel in rels:
                        props = {k: v for k, v in rel.properties.items()}
                        props_str = ", ".join(f"{k}: ${k}" for k in props.keys())
                        query = (
                            f"MATCH (a {{id: $source}}), (b {{id: $target}}) "
                            f"MERGE (a)-[r:{rel.rel_type.value}]->(b) "
                        )
                        if props_str:
                            query += f"SET r += {{{props_str}}}"
                        tx.run(query, {"source": rel.source_id, "target": rel.target_id, **props})

                return True
        except Exception as e:
            logger.error(f"批量创建失败: {e}")
            return False

    # =========================================================
    # 查询 - 因果链
    # =========================================================

    def find_causal_chain(self, event_id: str, max_depth: int = 3) -> list[dict]:
        """
        查找事件的因果链（前因→事件→后果）

        Args:
            event_id: 事件ID
            max_depth: 最大路径深度

        Returns:
            因果链列表
        """
        query = (
            f"MATCH path = (e:HistoricalEvent {{id: $event_id}})"
            f"<-[:PRECEDES*1..{max_depth}]-(cause)"
            f" RETURN cause, length(path) as depth"
            f" ORDER BY depth ASC"
        )
        result = self._run_query(query, {"event_id": event_id})

        causes = []
        if result:
            for record in result:
                node = dict(record["cause"])
                node["depth"] = record["depth"]
                causes.append(node)

        return causes

    def find_consequences(self, event_id: str, max_depth: int = 3) -> list[dict]:
        """查找事件的后果链"""
        query = (
            f"MATCH path = (e:HistoricalEvent {{id: $event_id}})"
            f"-[:RESULTS_IN*1..{max_depth}]->(result)"
            f" RETURN result, length(path) as depth"
            f" ORDER BY depth ASC"
        )
        result = self._run_query(query, {"event_id": event_id})

        consequences = []
        if result:
            for record in result:
                node = dict(record["result"])
                node["depth"] = record["depth"]
                consequences.append(node)

        return consequences

    def get_full_causal_network(self, event_id: str, depth: int = 2) -> dict:
        """
        获取事件的完整因果网络（前因+事件+后果）

        返回格式:
        {
            "event": {...},
            "causes": [{"node": {...}, "depth": 1}],
            "consequences": [{"node": {...}, "depth": 1}],
            "participants": [...],
            "related_knowledge": [...]
        }
        """
        # 获取事件本身
        event = self.get_node_by_id(event_id)
        if not event:
            return {"event": None, "causes": [], "consequences": [], "participants": []}

        # 获取前因
        causes = self.find_causal_chain(event_id, max_depth=depth)

        # 获取后果
        consequences = self.find_consequences(event_id, max_depth=depth)

        # 获取参与者
        query = (
            "MATCH (p:Person)-[:PARTICIPATED_IN|LED_BY]->(e:HistoricalEvent {id: $event_id}) "
            "RETURN p, type(r) AS role"
        )
        participants = []
        result = self._run_query(query, {"event_id": event_id})
        if result:
            for record in result:
                person = dict(record["p"])
                person["role"] = record["role"]
                participants.append(person)

        # 获取相关知识
        query = (
            "MATCH (e:HistoricalEvent {id: $event_id})<-[:RELATED_TO]-(kp:KnowledgePoint) "
            "RETURN kp LIMIT 5"
        )
        knowledge_points = []
        result = self._run_query(query, {"event_id": event_id})
        if result:
            for record in result:
                knowledge_points.append(dict(record["kp"]))

        return {
            "event": event,
            "causes": causes,
            "consequences": consequences,
            "participants": participants,
            "related_knowledge": knowledge_points,
        }

    # =========================================================
    # 查询 - 人物网络
    # =========================================================

    def find_person_events(self, person_id: str) -> list[dict]:
        """查找人物参与的所有事件"""
        query = (
            "MATCH (p:Person {id: $person_id})-[r:PARTICIPATED_IN|LED_BY]->(e:HistoricalEvent) "
            "RETURN e, type(r) AS role ORDER BY e.start_year"
        )
        result = self._run_query(query, {"person_id": person_id})

        events = []
        if result:
            for record in result:
                event = dict(record["e"])
                event["role"] = record["role"]
                events.append(event)
        return events

    def find_person_relationships(self, person_id: str) -> list[dict]:
        """查找人物与其他人的关系"""
        query = (
            "MATCH (p:Person {id: $person_id})-[r]-(other:Person) "
            "RETURN other, type(r) AS rel_type, properties(r) AS rel_props "
            "LIMIT 20"
        )
        result = self._run_query(query, {"person_id": person_id})

        relationships = []
        if result:
            for record in result:
                rel = {
                    "person": dict(record["other"]),
                    "type": record["rel_type"],
                }
                if record["rel_props"]:
                    rel.update(dict(record["rel_props"]))
                relationships.append(rel)
        return relationships

    def get_person_network(self, person_id: str) -> dict:
        """获取人物完整网络（参与事件+人物关系+所属朝代）"""
        person = self.get_node_by_id(person_id)
        if not person:
            return {"person": None, "events": [], "relationships": [], "dynasty": None}

        events = self.find_person_events(person_id)
        relationships = self.find_person_relationships(person_id)

        # 所属朝代
        dynasty = None
        query = "MATCH (p:Person {id: $person_id})-[:BELONGS_TO]->(d:Dynasty) RETURN d LIMIT 1"
        result = self._run_query(query, {"person_id": person_id})
        if result:
            dynasty = dict(result[0]["d"])

        return {
            "person": person,
            "events": events,
            "relationships": relationships,
            "dynasty": dynasty,
        }

    # =========================================================
    # 查询 - 朝代
    # =========================================================

    def get_dynasty_events(self, dynasty_name: str) -> list[dict]:
        """获取朝代的所有事件"""
        query = (
            "MATCH (d:Dynasty {name: $name})<-[:BELONGS_TO*0]-(e:HistoricalEvent) "
            "WHERE e.dynasty = $name "
            "RETURN e ORDER BY e.start_year"
        )
        result = self._run_query(query, {"name": dynasty_name})

        events = []
        if result:
            for record in result:
                events.append(dict(record["e"]))
        return events

    def get_dynasty_persons(self, dynasty_name: str) -> list[dict]:
        """获取朝代的人物"""
        query = (
            "MATCH (p:Person)-[:BELONGS_TO]->(d:Dynasty {name: $name}) "
            "RETURN p"
        )
        result = self._run_query(query, {"name": dynasty_name})

        persons = []
        if result:
            for record in result:
                persons.append(dict(record["p"]))
        return persons

    # =========================================================
    # 查询 - 知识点
    # =========================================================

    def find_related_knowledge(self, knowledge_id: str) -> list[dict]:
        """查找关联知识点"""
        query = (
            "MATCH (k1:KnowledgePoint {id: $kp_id})-[:RELATED_TO|REQUIRES]-(k2:KnowledgePoint) "
            "RETURN k2, type(r) AS rel_type LIMIT 10"
        )
        result = self._run_query(query, {"kp_id": knowledge_id})

        related = []
        if result:
            for record in result:
                kp = dict(record["k2"])
                kp["relation"] = record["rel_type"]
                related.append(kp)
        return related

    def get_learning_path(self, knowledge_id: str) -> list[dict]:
        """获取学习路径（前置依赖链）"""
        query = (
            "MATCH path = (k:KnowledgePoint {id: $kp_id})<-[:REQUIRES*]-(prereq) "
            "RETURN prereq, length(path) AS depth ORDER BY depth ASC"
        )
        result = self._run_query(query, {"kp_id": knowledge_id})

        path = []
        if result:
            for record in result:
                kp = dict(record["prereq"])
                kp["depth"] = record["depth"]
                path.append(kp)
        return path

    # =========================================================
    # 统计查询
    # =========================================================

    def count_nodes(self) -> dict[str, int]:
        """统计各类型节点数量"""
        query = (
            "MATCH (n) "
            "WITH labels(n)[0] AS label, count(n) AS cnt "
            "RETURN label, cnt ORDER BY cnt DESC"
        )
        result = self._run_query(query)
        if result:
            return {r["label"]: r["cnt"] for r in result}
        return {}

    def count_relationships(self) -> dict[str, int]:
        """统计关系数量"""
        query = (
            "MATCH ()-[r]->() "
            "WITH type(r) AS rel_type, count(r) AS cnt "
            "RETURN rel_type, cnt ORDER BY cnt DESC"
        )
        result = self._run_query(query)
        if result:
            return {r["rel_type"]: r["cnt"] for r in result}
        return {}

    def search_nodes(self, keyword: str, limit: int = 10) -> list[dict]:
        """全文搜索节点"""
        query = (
            "MATCH (n) "
            "WHERE n.name CONTAINS $keyword OR n.title CONTAINS $keyword OR n.description CONTAINS $keyword "
            "RETURN n, labels(n)[0] AS label LIMIT $limit"
        )
        result = self._run_query(query, {"keyword": keyword, "limit": limit})

        nodes = []
        if result:
            for record in result:
                node = dict(record["n"])
                node["_label"] = record["label"]
                nodes.append(node)
        return nodes


def get_kg_repository() -> KnowledgeGraphRepository:
    """获取知识图谱仓库实例"""
    return KnowledgeGraphRepository()
