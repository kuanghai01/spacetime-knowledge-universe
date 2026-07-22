"""
测试 - 数学 Agent 模块
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.agents.math_agent import (
    MathAgent,
    MathKnowledgeBase,
    MathDomain,
    Visualization,
)


class TestMathKnowledgeBase:
    """数学知识库测试"""

    @pytest.fixture
    def kb(self):
        return MathKnowledgeBase()

    @pytest.mark.asyncio
    async def test_search_algebra(self, kb):
        """测试代数知识点搜索"""
        results = await kb.search("解方程")
        assert len(results) >= 1
        assert any("方程" in r["title"] for r in results)

    @pytest.mark.asyncio
    async def test_search_geometry(self, kb):
        """测试几何知识点搜索"""
        results = await kb.search("三角形内角")
        assert len(results) >= 1
        assert any("三角形" in r["title"] for r in results)

    @pytest.mark.asyncio
    async def test_search_function(self, kb):
        """测试函数知识点搜索"""
        results = await kb.search("一次函数")
        assert len(results) >= 1
        assert any(r["domain"] == MathDomain.FUNCTION for r in results)

    @pytest.mark.asyncio
    async def test_search_by_domain(self, kb):
        """测试按领域搜索"""
        results = await kb.search("三角形")
        assert len(results) >= 1
        assert any(r["domain"] == MathDomain.GEOMETRY for r in results)

    @pytest.mark.asyncio
    async def test_get_by_id(self, kb):
        """测试根据ID获取"""
        result = await kb.get_by_id("math_001")
        assert result is not None
        assert result["title"] == "数轴与相反数"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, kb):
        """测试获取不存在的ID"""
        result = await kb.get_by_id("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_chapter_knowledge_number(self, kb):
        """测试获取数与代数章节"""
        results = await kb.get_chapter_knowledge("数与代数")
        assert len(results) >= 3

    @pytest.mark.asyncio
    async def test_get_chapter_knowledge_geometry(self, kb):
        """测试获取图形与几何章节"""
        results = await kb.get_chapter_knowledge("图形与几何")
        assert len(results) >= 1

    def test_get_visualizations_by_knowledge(self, kb):
        """测试根据知识点获取可视化"""
        visualizations = kb.get_visualizations_by_knowledge(["math_001"])
        assert len(visualizations) >= 1

    def test_get_visualizations_by_domain(self, kb):
        """测试根据分支获取可视化"""
        visualizations = kb.get_visualizations_by_domain(MathDomain.GEOMETRY)
        assert len(visualizations) >= 1
        assert all(vis.domain == MathDomain.GEOMETRY for vis in visualizations)


class TestMathAgent:
    """数学 Agent 测试"""

    @pytest.fixture
    def agent(self):
        with patch('src.agents.base_agent.ChatOpenAI'):
            return MathAgent()

    def test_agent_init(self, agent):
        """测试Agent初始化"""
        assert agent.subject_id == "math"
        assert agent.subject_name == "数学"
        assert agent.knowledge_base is not None

    def test_system_prompt(self, agent):
        """测试系统提示词"""
        from src.agents.base_agent import AgentContext
        prompt = agent.get_system_prompt(AgentContext(user_id="test"))
        assert "数学" in prompt
        assert "数先生" in prompt

    def test_is_visualization_request(self, agent):
        """测试可视化请求识别"""
        assert agent._is_visualization_request("画个图看看") is True
        assert agent._is_visualization_request("演示一下图像") is True
        assert agent._is_visualization_request("方程是什么") is False

    def test_is_problem_solving(self, agent):
        """测试解题请求识别"""
        assert agent._is_problem_solving("解方程") is True
        assert agent._is_problem_solving("计算过程") is True
        assert agent._is_problem_solving("什么是方程") is False

    def test_format_visualization(self, agent):
        """测试可视化格式化"""
        from src.agents.base_agent import AgentContext
        vis = Visualization(
            id="test_viz",
            title="测试可视化",
            domain=MathDomain.ALGEBRA,
            description="测试描述",
            steps=["步骤1", "步骤2"],
            conclusion="测试结论",
        )
        content = agent._format_visualization(vis, AgentContext(user_id="test"))
        assert "测试可视化" in content
        assert "步骤1" in content
        assert "测试结论" in content

    def test_extract_domain_tags(self, agent):
        """测试分支标签提取"""
        # 代数
        tags = agent._extract_domain_tags("解方程不等式")
        assert "代数" in tags

        # 几何
        tags = agent._extract_domain_tags("三角形面积")
        assert "几何" in tags

        # 函数
        tags = agent._extract_domain_tags("一次函数图像")
        assert "函数" in tags

    def test_suggest_visualizations(self, agent):
        """测试可视化推荐"""
        suggestions = agent._suggest_visualizations("一次函数的图像")
        assert isinstance(suggestions, list)

    @pytest.mark.asyncio
    async def test_handle_visualization_request(self, agent):
        """测试可视化请求处理"""
        mock_response = MagicMock()
        mock_response.content = "这是可视化演示..."

        with patch.object(agent.llm, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response

            response = await agent.handle("画个数轴看看", {"user_id": "test"})
            assert response["metadata"]["subject"] == "math"

    @pytest.mark.asyncio
    async def test_handle_problem_solving(self, agent):
        """测试解题请求处理"""
        mock_response = MagicMock()
        mock_response.content = "解方程的步骤如下..."

        with patch.object(agent.llm, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response

            response = await agent.handle("解方程2x+5=13", {"user_id": "test"})
            assert response["metadata"]["subject"] == "math"
            assert "exp_gained" in response

    @pytest.mark.asyncio
    async def test_handle_general_question(self, agent):
        """测试普通问题处理"""
        mock_response = MagicMock()
        mock_response.content = "这是一个数学概念..."

        with patch.object(agent.llm, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response

            response = await agent.handle("什么是勾股定理", {"user_id": "test"})
            assert response["metadata"]["subject"] == "math"
            assert "related_knowledge" in response


class TestVisualization:
    """可视化数据类测试"""

    def test_visualization_data_structure(self):
        """测试数据结构完整性"""
        vis = Visualization(
            id="test_001",
            title="测试",
            domain=MathDomain.ALGEBRA,
            description="描述",
            steps=["步骤1"],
            conclusion="结论",
            related_knowledge=["kp1"],
        )
        assert vis.difficulty == 1
        assert len(vis.steps) == 1
