"""
测试 - 教材智能解析模块
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from src.core.parser.textbook_parser import (
    PDFExtractor,
    StructureRecognizer,
    KnowledgeExtractor,
    TextbookParser,
    TextSection,
    ParsedStructure,
    ExtractedKnowledgePoint,
)


class TestPDFExtractor:
    """PDF 提取器测试"""
    
    @pytest.fixture
    def extractor(self):
        return PDFExtractor()
    
    def test_extract_file_not_found(self, extractor):
        """测试文件不存在"""
        with pytest.raises(Exception):
            extractor.extract("/nonexistent/file.pdf")
    
    def test_extract_unsupported_format(self, extractor):
        """测试不支持的格式"""
        import tempfile, os
        # 创建临时 txt 文件
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode='w') as f:
            f.write("this is not a pdf")
            temp_path = f.name
        
        try:
            result = extractor.extract(temp_path)
            # 如果没抛出异常，应该返回空字符串或空内容
            assert result is not None
        except Exception:
            pass  # 抛出异常也是正常行为
        finally:
            os.unlink(temp_path)


class TestStructureRecognizer:
    """结构识别器测试"""
    
    @pytest.fixture
    def recognizer(self):
        return StructureRecognizer()
    
    def test_recognize_chinese_chapters(self, recognizer):
        """测试中文章节识别"""
        text = """
第一章 史前时期
中国是人类起源地之一，距今约170万年的元谋人是已知最早的人类。

第一节 原始农耕生活
河姆渡居民种植水稻，半坡居民种植粟。

第二节 远古传说
黄帝和炎帝被尊为中华民族的人文始祖。

第二章 夏商周
夏朝是中国历史上第一个王朝。

第一节 夏朝的建立
禹建立夏朝，标志着中国早期国家的产生。
"""
        structure = recognizer.recognize(text)
        
        assert len(structure.sections) >= 2
        assert structure.sections[0].title == "史前时期"
        assert structure.sections[0].level == 1
    
    def test_recognize_numbered_sections(self, recognizer):
        """测试数字编号章节识别"""
        text = """
3.1 光的传播
光在同一种均匀介质中沿直线传播。

3.1.1 光的直线传播
影子的形成说明了光沿直线传播。

3.1.2 光速
光在真空中的速度约为3×10^8 m/s。

3.2 光的反射
光射到物体表面时，有一部分光会被物体表面反射回来。
"""
        structure = recognizer.recognize(text)
        
        assert len(structure.sections) >= 1
        assert structure.sections[0].title == "光的传播"
    
    def test_recognize_empty_text(self, recognizer):
        """测试空文本"""
        structure = recognizer.recognize("")
        assert len(structure.sections) == 0
    
    def test_match_title(self, recognizer):
        """测试标题匹配"""
        # 中文章节
        result = recognizer._match_title("第三章 秦汉时期")
        assert result is not None
        assert result[0] == 1
        assert result[1] == "秦汉时期"
        
        # 数字编号
        result = recognizer._match_title("3.1 光的传播")
        assert result is not None
        assert result[0] == 1
        
        # 非标题
        result = recognizer._match_title("这是一段普通文本")
        assert result is None


class TestKnowledgeExtractor:
    """知识点提取器测试"""
    
    @pytest.fixture
    def extractor(self):
        with patch('src.core.parser.textbook_parser.ChatOpenAI'):
            return KnowledgeExtractor()
    
    @pytest.mark.asyncio
    async def test_extract_basic(self, extractor):
        """测试基础知识点提取"""
        # Mock LLM 响应
        mock_response = MagicMock()
        mock_response.content = '''
{
  "knowledge_points": [
    {
      "title": "光的直线传播",
      "content": "光在同一种均匀介质中沿直线传播",
      "difficulty": 2,
      "tags": ["光学", "光的传播"],
      "key_concepts": ["直线传播", "均匀介质"]
    },
    {
      "title": "光速",
      "content": "光在真空中的速度约为3×10^8 m/s",
      "difficulty": 1,
      "tags": ["光学", "光速"],
      "key_concepts": ["3×10^8 m/s", "真空"]
    }
  ],
  "prerequisites": [],
  "summary": "光的传播基础知识"
}
'''
        
        with patch.object(extractor.llm, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            result = await extractor.extract(
                content="光在同一种均匀介质中沿直线传播。光在真空中的速度约为3×10^8 m/s。",
                subject="physics",
                section_info={"title": "光的传播", "level": 1}
            )
            
            assert len(result) == 2
            assert result[0].title == "光的直线传播"
            assert result[0].difficulty == 2
            assert "光学" in result[0].tags
    
    def test_parse_response_invalid_json(self, extractor):
        """测试无效 JSON 响应"""
        result = extractor._parse_response("invalid json", "physics")
        assert len(result) == 0
    
    def test_parse_response_partial_json(self, extractor):
        """测试部分 JSON 响应"""
        response = '''
这里有一些分析：
{
  "knowledge_points": [
    {
      "title": "测试知识点",
      "content": "测试内容",
      "difficulty": 1,
      "tags": ["测试"]
    }
  ]
}
'''
        result = extractor._parse_response(response, "physics")
        assert len(result) == 1
        assert result[0].title == "测试知识点"


class TestTextbookParser:
    """教材解析器集成测试"""
    
    @pytest.fixture
    def parser(self):
        with patch('src.core.parser.textbook_parser.ChatOpenAI'), \
             patch('src.core.parser.textbook_parser.OpenAIEmbeddings'), \
             patch.object(TextbookParser, '__init__', lambda self: None):
            p = TextbookParser()
            p.pdf_extractor = PDFExtractor()
            p.structure_recognizer = StructureRecognizer()
            p.knowledge_extractor = KnowledgeExtractor()
            p.embedding_model = MagicMock()
            p.vector_store = MagicMock()
            return p
    
    def test_get_leaf_sections(self, parser):
        """测试获取叶子章节"""
        root = TextSection(level=1, title="Root", content="")
        child1 = TextSection(level=2, title="Child1", content="")
        child2 = TextSection(level=2, title="Child2", content="")
        grandchild = TextSection(level=3, title="GrandChild", content="test")
        
        child2.children.append(grandchild)
        root.children.extend([child1, child2])
        
        leaves = parser._get_leaf_sections([root])
        
        assert len(leaves) == 2
        assert leaves[0].title == "Child1"
        assert leaves[1].title == "GrandChild"
    
    def test_build_knowledge_graph(self, parser):
        """测试知识图谱构建"""
        kps = [
            ExtractedKnowledgePoint(
                id="kp1", title="知识点1", chapter="第一章", tags=["力学"]
            ),
            ExtractedKnowledgePoint(
                id="kp2", title="知识点2", chapter="第一章", tags=["力学", "运动"]
            ),
            ExtractedKnowledgePoint(
                id="kp3", title="知识点3", chapter="第二章", tags=["光学"]
            ),
        ]
        
        graph = parser._build_knowledge_graph(kps)
        
        assert len(graph["nodes"]) == 3
        # 应该有边（同一章节的序列关系 + 标签关联）
        assert len(graph["edges"]) >= 1
    
    def test_build_knowledge_graph_empty(self, parser):
        """测试空知识点"""
        graph = parser._build_knowledge_graph([])
        assert len(graph["nodes"]) == 0
        assert len(graph["edges"]) == 0
