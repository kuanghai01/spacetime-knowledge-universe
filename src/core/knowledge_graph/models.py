"""
知识图谱 - 实体模型

节点类型:
- Subject: 学科
- HistoricalEvent: 历史事件
- Person: 历史人物
- Dynasty: 朝代
- KnowledgePoint: 知识点
- Concept: 核心概念

关系类型:
- BELONGS_TO: 人物属于朝代
- PARTICIPATED_IN: 人物参与事件
- LED_BY: 事件领导者
- PRECEDES: 事件前因
- RESULTS_IN: 事件后果
- LOCATED_AT: 事件发生地
- BELONGS_TO_SUBJECT: 知识点属于学科
- REQUIRES: 知识点前置依赖
- RELATED_TO: 知识点关联
- TEACHES: 学科教授知识点
"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class NodeType(str, Enum):
    """节点类型"""
    SUBJECT = "Subject"
    HISTORICAL_EVENT = "HistoricalEvent"
    PERSON = "Person"
    DYNASTY = "Dynasty"
    KNOWLEDGE_POINT = "KnowledgePoint"
    CONCEPT = "Concept"
    LOCATION = "Location"


class RelationshipType(str, Enum):
    """关系类型"""
    BELONGS_TO = "BELONGS_TO"
    PARTICIPATED_IN = "PARTICIPATED_IN"
    LED_BY = "LED_BY"
    PRECEDES = "PRECEDES"
    RESULTS_IN = "RESULTS_IN"
    LOCATED_AT = "LOCATED_AT"
    BELONGS_TO_SUBJECT = "BELONGS_TO_SUBJECT"
    REQUIRES = "REQUIRES"
    RELATED_TO = "RELATED_TO"
    TEACHES = "TEACHES"
    PART_OF = "PART_OF"
    EVOLVED_FROM = "EVOLVED_FROM"


@dataclass
class GraphNode:
    """图谱节点基类"""
    id: str
    label: NodeType
    properties: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"id": self.id, "label": self.label.value, **self.properties}


@dataclass
class GraphRelationship:
    """图谱关系"""
    source_id: str
    target_id: str
    rel_type: RelationshipType
    properties: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.rel_type.value,
            **self.properties,
        }


@dataclass
class Subject:
    """学科节点"""
    name: str
    description: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"subject_{self.name}"

    def to_node(self) -> GraphNode:
        return GraphNode(
            id=self.id,
            label=NodeType.SUBJECT,
            properties={
                "name": self.name,
                "description": self.description,
            },
        )


@dataclass
class HistoricalEvent:
    """历史事件节点"""
    id: str
    name: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    description: str = ""
    location: str = ""
    dynasty: str = ""
    importance: int = 1  # 1-5，重要性评分

    def to_node(self) -> GraphNode:
        props = {
            "name": self.name,
            "description": self.description,
            "dynasty": self.dynasty,
            "importance": self.importance,
        }
        if self.start_year is not None:
            props["start_year"] = self.start_year
        if self.end_year is not None:
            props["end_year"] = self.end_year
        if self.location:
            props["location"] = self.location

        return GraphNode(
            id=self.id,
            label=NodeType.HISTORICAL_EVENT,
            properties=props,
        )


@dataclass
class Person:
    """历史人物节点"""
    id: str
    name: str
    dynasty: str = ""
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    title: str = ""
    description: str = ""

    def to_node(self) -> GraphNode:
        props = {"name": self.name, "dynasty": self.dynasty}
        if self.title:
            props["title"] = self.title
        if self.birth_year is not None:
            props["birth_year"] = self.birth_year
        if self.death_year is not None:
            props["death_year"] = self.death_year
        if self.description:
            props["description"] = self.description

        return GraphNode(
            id=self.id,
            label=NodeType.PERSON,
            properties=props,
        )


@dataclass
class Dynasty:
    """朝代节点"""
    name: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    capital: str = ""
    description: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"dynasty_{self.name}"

    id: str = ""

    def to_node(self) -> GraphNode:
        props = {"name": self.name}
        if self.start_year is not None:
            props["start_year"] = self.start_year
        if self.end_year is not None:
            props["end_year"] = self.end_year
        if self.capital:
            props["capital"] = self.capital
        if self.description:
            props["description"] = self.description

        return GraphNode(
            id=self.id,
            label=NodeType.DYNASTY,
            properties=props,
        )


@dataclass
class KnowledgePoint:
    """知识点节点"""
    id: str
    title: str
    content: str = ""
    subject_id: str = ""
    difficulty: int = 1
    chapter: str = ""

    def to_node(self) -> GraphNode:
        props = {
            "title": self.title,
            "difficulty": self.difficulty,
        }
        if self.content:
            props["content"] = self.content
        if self.chapter:
            props["chapter"] = self.chapter
        if self.subject_id:
            props["subject_id"] = self.subject_id

        return GraphNode(
            id=self.id,
            label=NodeType.KNOWLEDGE_POINT,
            properties=props,
        )


@dataclass
class Location:
    """地理位置节点"""
    id: str
    name: str
    modern_name: str = ""
    description: str = ""

    def to_node(self) -> GraphNode:
        props = {"name": self.name}
        if self.modern_name:
            props["modern_name"] = self.modern_name
        if self.description:
            props["description"] = self.description

        return GraphNode(
            id=self.id,
            label=NodeType.LOCATION,
            properties=props,
        )
