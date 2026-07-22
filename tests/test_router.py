"""
测试 - 中枢校长 Agent
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from config.settings import settings
from src.core.router.principal_agent import (
    PrincipalAgent,
    IntentClassifier,
    SubjectRouter,
    ContextManager,
    UserContext,
    IntentType,
)


class TestIntentClassifier:
    """意图分类器测试（基类逻辑）"""
    
    @pytest.fixture
    def classifier(self):
        with patch('src.core.router.principal_agent.ChatOpenAI'):
            return IntentClassifier()
    
    def test_classifier_init(self, classifier):
        """测试分类器初始化"""
        assert classifier.llm is not None
        assert classifier.prompt is not None
    
    def test_supported_subjects(self, classifier):
        """测试支持的学科列表"""
        assert "history" in settings.AVAILABLE_SUBJECTS
        assert "physics" in settings.AVAILABLE_SUBJECTS
        assert "math" in settings.AVAILABLE_SUBJECTS
        assert "chemistry" in settings.AVAILABLE_SUBJECTS


class TestSubjectRouter:
    """学科路由器测试"""
    
    @pytest.fixture
    def router(self):
        return SubjectRouter()
    
    @pytest.mark.asyncio
    async def test_route_explicit_subject(self, router):
        """测试明确指定学科"""
        intent_result = {"target_subject": "physics", "confidence": 0.9}
        context = UserContext(user_id="test_user")
        
        result = await router.route("力的作用", intent_result, context)
        assert result == "physics"
    
    @pytest.mark.asyncio
    async def test_route_current_subject(self, router):
        """测试使用当前学科"""
        intent_result = {"target_subject": None, "confidence": 0.5}
        context = UserContext(user_id="test_user", current_subject="history")
        
        result = await router.route("继续学习", intent_result, context)
        assert result == "history"
    
    @pytest.mark.asyncio
    async def test_route_keyword_matching(self, router):
        """测试关键词匹配"""
        intent_result = {"target_subject": None, "confidence": 0.5}
        context = UserContext(user_id="test_user")
        
        result = await router.route("这个化学方程式怎么配平？", intent_result, context)
        assert result == "chemistry"


class TestContextManager:
    """上下文管理器测试"""
    
    @pytest.fixture
    def manager(self):
        return ContextManager()
    
    def test_get_context_new_user(self, manager):
        """测试新用户上下文"""
        context = manager.get_context("new_user")
        assert context.user_id == "new_user"
        assert context.current_subject is None
        assert context.user_level == 1
    
    def test_update_context(self, manager):
        """测试更新上下文"""
        manager.get_context("test_user")
        manager.update_context("test_user", current_subject="history", user_level=5)
        
        context = manager.get_context("test_user")
        assert context.current_subject == "history"
        assert context.user_level == 5
    
    def test_add_conversation(self, manager):
        """测试添加对话历史"""
        manager.add_conversation("test_user", "user", "你好")
        manager.add_conversation("test_user", "assistant", "你好！有什么可以帮助你的？")
        
        context = manager.get_context("test_user")
        assert len(context.conversation_history) == 2
        assert context.conversation_history[0]["role"] == "user"


class TestPrincipalAgent:
    """中枢校长 Agent 测试"""
    
    @pytest.fixture
    def agent(self):
        with patch('src.core.router.principal_agent.ChatOpenAI'):
            return PrincipalAgent()
    
    @pytest.mark.asyncio
    async def test_dispatch_to_history(self, agent):
        """测试路由到历史学科"""
        # Mock 意图分类
        agent.intent_classifier.classify = AsyncMock(return_value={
            "intent_type": "subject_learning",
            "target_subject": "history",
            "confidence": 0.95,
            "related_subjects": []
        })
        
        result = await agent.dispatch("test_user", "秦始皇是谁？")
        
        assert result.target_agent == "history"
        assert result.mode == "single_subject"
        assert result.confidence >= 0.9
    
    @pytest.mark.asyncio
    async def test_dispatch_cross_subject(self, agent):
        """测试跨学科路由"""
        agent.intent_classifier.classify = AsyncMock(return_value={
            "intent_type": "cross_subject",
            "target_subject": "丝绸之路",
            "confidence": 0.85,
            "related_subjects": ["history", "geography"]
        })
        
        result = await agent.dispatch("test_user", "丝绸之路经过了哪些地方？")
        
        assert result.mode == "cross_subject"
        assert len(result.target_agents) >= 1
    
    def test_register_agent(self, agent):
        """测试注册学科 Agent"""
        mock_agent = MagicMock()
        agent.register_agent("test_subject", mock_agent)
        
        assert "test_subject" in agent.agent_registry
        assert agent.agent_registry["test_subject"] == mock_agent
