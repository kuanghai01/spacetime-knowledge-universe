"""
测试 - 知识图谱模块
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from src.core.knowledge_graph.models import (
    Subject,
    HistoricalEvent,
    Person,
    Dynasty,
    KnowledgePoint,
    Location,
    GraphNode,
    GraphRelationship,
    NodeType,
    RelationshipType,
)
from src.core.knowledge_graph.service import KnowledgeGraphService


class TestGraphModels:
    """图谱数据模型测试"""

    def test_subject_to_node(self):
        s = Subject(id="sub_1", name="数学", description="描述了")
        node = s.to_node()
        assert node.id == "sub_1"
        assert node.label == NodeType.SUBJECT
        assert node.properties["name"] == "数学"

    def test_historical_event_to_node(self):
        e = HistoricalEvent(
            id="evt_1", name="秦灭六国",
            start_year=-221, dynasty="秦朝",
        )
        node = e.to_node()
        assert node.label == NodeType.HISTORICAL_EVENT
        assert node.properties["start_year"] == -221

    def test_person_to_node(self):
        p = Person(id="p_1", name="秦始皇", dynasty="秦朝")
        node = p.to_node()
        assert node.label == NodeType.PERSON
        assert node.properties["name"] == "秦始皇"

    def test_dynasty_to_node(self):
        d = Dynasty(id="d_1", name="唐朝", start_year=618, end_year=907)
        node = d.to_node()
        assert node.label == NodeType.DYNASTY
        assert node.properties["start_year"] == 618

    def test_knowledge_point_to_node(self):
        kp = KnowledgePoint(id="kp_1", title="秦灭六国顺序", content="韩赵魏楚燕齐")
        node = kp.to_node()
        assert node.label == NodeType.KNOWLEDGE_POINT

    def test_location_to_node(self):
        loc = Location(id="loc_1", name="长安", modern_name="西安")
        node = loc.to_node()
        assert node.label == NodeType.LOCATION

    def test_graph_relationship(self):
        rel = GraphRelationship("a", "b", RelationshipType.PRECEDES)
        d = rel.to_dict()
        assert d["source"] == "a"
        assert d["target"] == "b"
        assert d["type"] == "PRECEDES"


class TestKnowledgeGraphService:
    """知识图谱服务测试"""

    @pytest.fixture
    def mock_repo(self):
        """Mock 仓库"""
        repo = MagicMock()
        return repo

    @pytest.fixture
    def service(self, mock_repo):
        svc = KnowledgeGraphService()
        svc.repo = mock_repo
        return svc

    def test_analyze_event_not_found(self, service, mock_repo):
        """测试事件未找到"""
        mock_repo.search_nodes.return_value = []
        result = service.analyze_event("不存在的事件")
        assert result is None

    def test_analyze_event_success(self, service, mock_repo):
        """测试事件分析"""
        mock_repo.search_nodes.return_value = [
            {
                "id": "evt_001",
                "name": "秦灭六国",
                "description": "统一六国",
                "start_year": -221,
                "dynasty": "秦朝",
                "_labels": ["HistoricalEvent"],
            }
        ]
        mock_repo.get_full_causal_network.return_value = {
            "event": {"id": "evt_001", "name": "秦灭六国"},
            "causes": [{"name": "商鞅变法", "depth": 1}],
            "consequences": [{"name": "秦朝建立", "depth": 1}],
            "participants": [{"name": "秦始皇", "role": "LED_BY"}],
            "related_knowledge": [{"title": "统一措施"}],
        }

        result = service.analyze_event("秦灭六国")
        assert result is not None
        assert result["event"]["name"] == "秦灭六国"
        assert len(result["causes"]) >= 1
        assert len(result["consequences"]) >= 1

    def test_analyze_person_not_found(self, service, mock_repo):
        """测试人物未找到"""
        mock_repo.search_nodes.return_value = []
        result = service.analyze_person("不存在的人")
        assert result is None

    def test_analyze_person_success(self, service, mock_repo):
        """测试人物分析"""
        mock_repo.search_nodes.return_value = [
            {
                "id": "p_001",
                "name": "秦始皇",
                "dynasty": "秦朝",
                "title": "始皇帝",
                "_labels": ["Person"],
            }
        ]
        mock_repo.get_person_network.return_value = {
            "person": {"id": "p_001", "name": "秦始皇"},
            "events": [{"name": "秦灭六国", "start_year": -221, "role": "LED_BY"}],
            "relationships": [],
            "dynasty": {"name": "秦朝", "start_year": -221, "end_year": -206},
        }

        result = service.analyze_person("秦始皇")
        assert result is not None
        assert result["person"]["name"] == "秦始皇"
        assert len(result["events"]) >= 1

    def test_format_causal_response(self, service, mock_repo):
        """测试因果分析响应格式化"""
        mock_repo.search_nodes.return_value = [
            {
                "id": "evt_001",
                "name": "秦朝灭亡",
                "description": "秦朝二世而亡",
                "start_year": -206,
                "dynasty": "秦朝",
                "_labels": ["HistoricalEvent"],
            }
        ]
        mock_repo.get_full_causal_network.return_value = {
            "event": {"id": "evt_001", "name": "秦朝灭亡"},
            "causes": [{"name": "暴政", "depth": 1}, {"name": "严刑峻法", "depth": 2}],
            "consequences": [{"name": "汉朝建立", "depth": 1}],
            "participants": [{"name": "刘邦", "role": "LED_BY"}],
            "related_knowledge": [{"title": "秦末农民起义"}],
        }

        response = service.format_causal_response("秦朝灭亡")
        assert "秦朝灭亡" in response
        assert "汉朝建立" in response
        assert "知识图谱" in response

    def test_format_causal_response_not_found(self, service, mock_repo):
        """测试未找到时的格式化响应"""
        mock_repo.search_nodes.return_value = []
        response = service.format_causal_response("不存在的事件")
        assert "没有找到" in response

    def test_get_graph_statistics(self, service, mock_repo):
        """测试图谱统计"""
        mock_repo.count_nodes.return_value = {"Person": 10, "HistoricalEvent": 15}
        mock_repo.count_relationships.return_value = {"BELONGS_TO": 8}

        stats = service.get_graph_statistics()
        assert "nodes" in stats
        assert "relationships" in stats

    def test_get_causal_explanation(self, service, mock_repo):
        """测试因果解释生成"""
        mock_repo.search_nodes.return_value = [
            {
                "id": "evt_001",
                "name": "商鞅变法",
                "description": "秦国变法图强",
                "start_year": -356,
                "dynasty": "战国",
                "_labels": ["HistoricalEvent"],
            }
        ]
        mock_repo.get_full_causal_network.return_value = {
            "event": {"id": "evt_001", "name": "商鞅变法"},
            "causes": [],
            "consequences": [{"name": "秦国强盛", "depth": 1}],
            "participants": [{"name": "商鞅", "role": "LED_BY"}],
            "related_knowledge": [],
        }

        explanation = service.get_causal_explanation("商鞅变法")
        assert explanation is not None
        assert "商鞅变法" in explanation

    def test_get_timeline(self, service, mock_repo):
        """测试朝代时间线"""
        mock_repo.get_dynasty_events.return_value = [
            {"name": "秦朝建立", "start_year": -221, "importance": 5},
        ]
        mock_repo.get_dynasty_persons.return_value = [
            {"name": "秦始皇", "title": "始皇帝"},
        ]

        timeline = service.get_timeline("秦朝")
        assert timeline is not None
        assert timeline["dynasty"] == "秦朝"
        assert len(timeline["events"]) >= 1

    def test_get_timeline_not_found(self, service, mock_repo):
        """测试朝代不存在"""
        mock_repo.get_dynasty_events.return_value = []
        mock_repo.get_dynasty_persons.return_value = []

        timeline = service.get_timeline("不存在")
        assert timeline is None
