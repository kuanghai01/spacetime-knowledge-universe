"""
测试 - 知识图谱种子数据
"""
import pytest
from unittest.mock import MagicMock, patch

from src.core.knowledge_graph.seed_data import seed_history_kg, get_seed_summary
from src.core.knowledge_graph.models import (
    Subject,
    HistoricalEvent,
    Person,
    Dynasty,
    KnowledgePoint,
    Location,
    GraphRelationship,
    RelationshipType,
)


class TestSeedData:
    """种子数据测试"""

    def test_seed_history_kg_with_mock(self):
        """测试种子数据填充（mock模式）"""
        with patch('src.core.knowledge_graph.seed_data.get_kg_repository') as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo_cls.return_value = mock_repo
            mock_repo.is_available = True
            mock_repo.create_node.return_value = True
            mock_repo.create_subject.return_value = True
            mock_repo.create_event.return_value = True
            mock_repo.create_person.return_value = True
            mock_repo.create_dynasty.return_value = True
            mock_repo.create_knowledge_point.return_value = True
            mock_repo.create_location.return_value = True
            mock_repo.create_relationship.return_value = True

            result = seed_history_kg()
            assert result is True

            # 验证创建了学科
            mock_repo.create_subject.assert_called()

            # 验证创建了朝代（至少8个）
            assert mock_repo.create_dynasty.call_count >= 8

            # 验证创建了事件（至少10个）
            assert mock_repo.create_event.call_count >= 10

            # 验证创建了人物（至少5个）
            assert mock_repo.create_person.call_count >= 5

            # 验证创建了关系（至少15个）
            assert mock_repo.create_relationship.call_count >= 15

    def test_seed_summary_with_mock(self):
        """测试种子数据统计"""
        with patch('src.core.knowledge_graph.seed_data.get_kg_repository') as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo_cls.return_value = mock_repo
            mock_repo.count_nodes.return_value = {"Person": 8, "HistoricalEvent": 15}
            mock_repo.count_relationships.return_value = {"BELONGS_TO": 8}

            summary = get_seed_summary()
            assert "nodes" in summary
            assert "relationships" in summary
