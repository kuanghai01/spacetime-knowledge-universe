"""
测试 - 物理 Agent 模块
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.agents.physics_agent import (
    PhysicsAgent,
    PhysicsKnowledgeBase,
    PhysicsDomain,
    VirtualExperiment,
)


class TestPhysicsKnowledgeBase:
    """物理知识库测试"""
    
    @pytest.fixture
    def kb(self):
        return PhysicsKnowledgeBase()
    
    @pytest.mark.asyncio
    async def test_search_mechanics(self, kb):
        """测试力学知识点搜索"""
        results = await kb.search("牛顿第一定律")
        assert len(results) >= 1
        assert any("牛顿" in r["title"] for r in results)
    
    @pytest.mark.asyncio
    async def test_search_optics(self, kb):
        """测试光学知识点搜索"""
        results = await kb.search("光的传播")
        assert len(results) >= 1
        assert any(r["domain"] == PhysicsDomain.OPTICS for r in results)
    
    @pytest.mark.asyncio
    async def test_search_electricity(self, kb):
        """测试电学知识点搜索"""
        results = await kb.search("电压电流")
        assert len(results) >= 1
        assert any(r["domain"] == PhysicsDomain.ELECTRICITY for r in results)
    
    @pytest.mark.asyncio
    async def test_search_by_domain(self, kb):
        """测试按领域搜索"""
        results = await kb.search("光的反射")
        # 应该优先返回光学领域的结果
        optics_results = [r for r in results if r["domain"] == PhysicsDomain.OPTICS]
        assert len(optics_results) >= 1
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, kb):
        """测试根据 ID 获取"""
        result = await kb.get_by_id("phy_001")
        assert result is not None
        assert result["title"] == "光的直线传播"
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, kb):
        """测试获取不存在的 ID"""
        result = await kb.get_by_id("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_chapter_knowledge(self, kb):
        """测试获取章节知识"""
        results = await kb.get_chapter_knowledge("第二章 光学")
        assert len(results) >= 3  # 光学章节有多个知识点
    
    def test_get_experiments_by_knowledge(self, kb):
        """测试根据知识点获取实验"""
        experiments = kb.get_experiments_by_knowledge(["phy_001", "phy_002"])
        assert len(experiments) >= 1
    
    def test_get_experiments_by_domain(self, kb):
        """测试根据物理分支获取实验"""
        experiments = kb.get_experiments_by_domain(PhysicsDomain.OPTICS)
        assert len(experiments) >= 1
        assert all(exp.domain == PhysicsDomain.OPTICS for exp in experiments)


class TestPhysicsAgent:
    """物理 Agent 测试"""
    
    @pytest.fixture
    def agent(self):
        with patch('src.agents.base_agent.ChatOpenAI'):
            return PhysicsAgent()
    
    def test_agent_init(self, agent):
        """测试 Agent 初始化"""
        assert agent.subject_id == "physics"
        assert agent.subject_name == "物理"
        assert agent.knowledge_base is not None
    
    def test_system_prompt(self, agent):
        """测试系统提示词生成"""
        from src.agents.base_agent import AgentContext
        prompt = agent.get_system_prompt(AgentContext(user_id="test"))
        assert "物理" in prompt
        assert "物先生" in prompt
    
    def test_is_experiment_request(self, agent):
        """测试实验请求识别"""
        assert agent._is_experiment_request("做个实验看看") is True
        assert agent._is_experiment_request("演示一下这个过程") is True
        assert agent._is_experiment_request("折射定律是什么") is False
    
    def test_format_experiment(self, agent):
        """测试实验格式化"""
        exp = VirtualExperiment(
            id="test_exp",
            title="测试实验",
            domain=PhysicsDomain.MECHANICS,
            description="这是一个测试实验",
            principle="测试原理",
            steps=["步骤1", "步骤2"],
            observations=["观察1", "观察2"],
            related_knowledge=["kp_001"],
        )
        content = agent._format_experiment(exp, {})
        assert "测试实验" in content
        assert "步骤1" in content
        assert "观察1" in content
    
    def test_extract_domain_tags(self, agent):
        """测试领域标签提取"""
        # 力学
        tags = agent._extract_domain_tags("牛顿力和运动")
        assert "力学" in tags
        
        # 光学
        tags = agent._extract_domain_tags("光的反射折射")
        assert "光学" in tags
        
        # 多领域
        tags = agent._extract_domain_tags("光学和电学")
        assert "光学" in tags
        assert "电学" in tags
    
    def test_suggest_experiments(self, agent):
        """测试实验建议"""
        suggestions = agent._suggest_experiments("光的传播")
        # 应该返回至少一个实验建议
        assert isinstance(suggestions, list)
    
    @pytest.mark.asyncio
    async def test_handle_experiment_request(self, agent):
        """测试处理实验请求"""
        # Mock LLM
        mock_response = MagicMock()
        mock_response.content = "这是虚拟实验的演示..."
        
        with patch.object(agent.llm, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            response = await agent.handle("做个光的实验", {"user_id": "test"})
            assert response["metadata"]["subject"] == "physics"
    
    @pytest.mark.asyncio
    async def test_handle_knowledge_question(self, agent):
        """测试处理知识问题"""
        mock_response = MagicMock()
        mock_response.content = "光在同一种均匀介质中沿直线传播..."
        
        with patch.object(agent.llm, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            response = await agent.handle("光是怎么传播的？", {"user_id": "test"})
            assert response["metadata"]["subject"] == "physics"
            assert "exp_gained" in response


class TestVirtualExperiment:
    """虚拟实验数据类测试"""
    
    def test_experiment_data_structure(self):
        """测试实验数据结构完整性"""
        exp = VirtualExperiment(
            id="test_001",
            title="测试实验",
            domain=PhysicsDomain.MECHANICS,
            description="描述",
            principle="原理",
            steps=["步骤1"],
            observations=["观察1"],
            related_knowledge=["kp1"],
        )
        assert exp.difficulty == 1
        assert len(exp.steps) == 1
