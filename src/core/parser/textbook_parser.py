"""
教材智能解析模块

核心能力:
1. PDF 文本提取与结构识别
2. 知识点智能提取（NLP + LLM）
3. 知识图谱关联构建
4. 向量化存储（Milvus）
"""
import re
import logging
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class TextSection:
    """文本章节"""
    level: int  # 标题层级 1-4
    title: str
    content: str
    parent: Optional['TextSection'] = None
    children: list['TextSection'] = field(default_factory=list)


@dataclass
class ParsedStructure:
    """解析后的文档结构"""
    title: str = ""
    publisher: str = ""
    grade: str = ""
    sections: list[TextSection] = field(default_factory=list)
    total_chars: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class ExtractedKnowledgePoint:
    """提取的知识点"""
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    content: str = ""
    chapter: str = ""
    section: str = ""
    difficulty: int = 1
    tags: list[str] = field(default_factory=list)
    embedding: Optional[list[float]] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ParseResult:
    """解析结果"""
    textbook_id: str = field(default_factory=lambda: str(uuid4()))
    success: bool = False
    structure: Optional[ParsedStructure] = None
    knowledge_points: list[ExtractedKnowledgePoint] = field(default_factory=list)
    knowledge_graph: dict = field(default_factory=dict)
    error_message: str = ""


class PDFExtractor:
    """PDF 文本提取器"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    def extract(self, file_path: str) -> str:
        """
        提取 PDF 文本
        
        Args:
            file_path: PDF 文件路径
            
        Returns:
            提取的纯文本
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("请安装 PyMuPDF: pip install pymupdf")
        
        doc = fitz.open(file_path)
        text_parts = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                text_parts.append(f"\n--- 第{page_num + 1}页 ---\n{text}")
        
        doc.close()
        return "\n".join(text_parts)
    
    def extract_with_metadata(self, file_path: str) -> dict:
        """提取 PDF 元数据"""
        import fitz
        
        doc = fitz.open(file_path)
        metadata = doc.metadata
        page_count = len(doc)
        doc.close()
        
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "page_count": page_count,
        }


class StructureRecognizer:
    """文档结构识别器"""
    
    # 常见标题模式
    TITLE_PATTERNS = [
        r'^第[一二三四五六七八九十百千]+章\s+(.+)',  # 第三章 xxx
        r'^第[一二三四五六七八九十百千]+节\s+(.+)',  # 第三节 xxx
        r'^第[一二三四五六七八九十百千]+课\s+(.+)',  # 第三课 xxx
        r'^\d+\.\d+\s+(.+)',  # 3.1 xxx
        r'^\d+\.\d+\.\d+\s+(.+)',  # 3.1.1 xxx
        r'^[（(]\d[)）]\s*(.+)',  # （1）xxx
        r'^\d+\s+(.+)',  # 3 xxx
    ]
    
    def recognize(self, text: str) -> ParsedStructure:
        """
        识别文档结构
        
        Args:
            text: PDF 提取的文本
            
        Returns:
            解析后的文档结构
        """
        structure = ParsedStructure()
        lines = text.split('\n')
        
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是标题
            title_info = self._match_title(line)
            if title_info:
                # 保存上一个章节
                if current_section:
                    current_section.content = '\n'.join(current_content).strip()
                
                level, title = title_info
                section = TextSection(level=level, title=title, content="")
                
                # 建立父子关系
                if current_section and level > current_section.level:
                    section.parent = current_section
                    current_section.children.append(section)
                elif current_section and level <= current_section.level:
                    # 找到合适的父节点
                    parent = current_section.parent
                    while parent and parent.level >= level:
                        parent = parent.parent
                    if parent:
                        section.parent = parent
                        parent.children.append(section)
                    else:
                        structure.sections.append(section)
                else:
                    structure.sections.append(section)
                
                current_section = section
                current_content = []
            else:
                # 普通内容
                current_content.append(line)
                structure.total_chars += len(line)
        
        # 保存最后一个章节
        if current_section:
            current_section.content = '\n'.join(current_content).strip()
        
        return structure
    
    def _match_title(self, line: str) -> Optional[tuple[int, str]]:
        """匹配标题模式"""
        for pattern in self.TITLE_PATTERNS:
            match = re.match(pattern, line)
            if match:
                title = match.group(1) if match.groups() else line
                level = self._estimate_level(pattern)
                return level, title
        return None
    
    def _estimate_level(self, pattern: str) -> int:
        """估计标题层级（基于模式在列表中的位置）"""
        for idx, p in enumerate(self.TITLE_PATTERNS):
            if p == pattern:
                if '章' in p:
                    return 1
                elif '节' in p or '课' in p:
                    return 2
                elif p == self.TITLE_PATTERNS[3]:  # ^\d+\.\d+\s+(.+)
                    return 1
                elif p == self.TITLE_PATTERNS[4]:  # ^\d+\.\d+\.\d+\s+(.+)
                    return 2
                else:
                    return 3
        return 2


class KnowledgeExtractor:
    """知识点提取器（基于 LLM）"""
    
    SYSTEM_PROMPT = """你是一个智能教育内容解析专家。
请从给定的教材章节中提取核心知识点，并按照以下 JSON 格式返回：

```json
{{
  "knowledge_points": [
    {{
      "title": "知识点标题",
      "content": "知识点内容（200字以内）",
      "difficulty": 1-5,
      "tags": ["标签1", "标签2"],
      "key_concepts": ["核心概念1", "核心概念2"]
    }}
  ],
  "prerequisites": ["前置知识点标题"],
  "summary": "本章节核心内容摘要（50字以内）"
}}
```

提取规则:
1. 每个知识点应该是独立的学习单元
2. 标题应简洁明确，便于记忆
3. 内容应包含核心定义、原理或事实
4. 难度根据内容复杂度评级（1最简，5最难）
5. 标签用于关联和检索
6. 知识点数量控制在 3-8 个
"""
    
    def __init__(self):
        self.llm = None
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.3,
                api_key=settings.OPENAI_API_KEY
            )
    
    async def extract(
        self,
        content: str,
        subject: str,
        section_info: dict = None
    ) -> list[ExtractedKnowledgePoint]:
        """
        从章节内容中提取知识点
        
        Args:
            content: 章节文本
            subject: 学科 ID
            section_info: 章节信息（标题、层级等）
            
        Returns:
            提取的知识点列表
        """
        # 限制内容长度
        truncated_content = content[:4000]
        
        prompt = f"""【学科】: {subject}
【章节】: {section_info.get('title', '未知') if section_info else '未知'}
【内容】:
{truncated_content}

请提取核心知识点。"""
        
        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # 解析响应
        return self._parse_response(response.content, subject, section_info)
    
    def _parse_response(
        self,
        content: str,
        subject: str,
        section_info: dict = None
    ) -> list[ExtractedKnowledgePoint]:
        """解析 LLM 响应"""
        import json
        
        result = []
        
        try:
            # 提取 JSON 部分
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(content)
            
            for kp_data in data.get("knowledge_points", []):
                kp = ExtractedKnowledgePoint(
                    title=kp_data.get("title", ""),
                    content=kp_data.get("content", ""),
                    chapter=section_info.get("title", "") if section_info else "",
                    difficulty=kp_data.get("difficulty", 1),
                    tags=kp_data.get("tags", []),
                    metadata={
                        "subject": subject,
                        "key_concepts": kp_data.get("key_concepts", []),
                        "extracted_at": datetime.now().isoformat()
                    }
                )
                result.append(kp)
        
        except Exception as e:
            logger.warning(f"Failed to parse knowledge extraction response: {e}")
        
        return result


class VectorStore:
    """向量存储（基于 Milvus）"""
    
    def __init__(self):
        self.collection_name = "knowledge_points"
        self._init_collection()
    
    def _init_collection(self):
        """初始化 Milvus 集合"""
        try:
            from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
            
            # 连接 Milvus
            connections.connect(
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT
            )
            
            # 如果集合不存在则创建
            if not utility.has_collection(self.collection_name):
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=36, is_primary=True),
                    FieldSchema(name="subject_id", dtype=DataType.VARCHAR, max_length=50),
                    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=200),
                    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="chapter_id", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=500),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
                ]
                
                schema = CollectionSchema(fields, "知识点向量集合")
                collection = Collection(self.collection_name, schema)
                
                # 创建索引
                index_params = {
                    "metric_type": "COSINE",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 1024}
                }
                collection.create_index("embedding", index_params)
                collection.load()
                
                logger.info(f"Milvus collection '{self.collection_name}' created")
        
        except Exception as e:
            logger.warning(f"Milvus initialization failed: {e}")
    
    async def insert(self, knowledge_points: list[ExtractedKnowledgePoint]):
        """插入知识点向量"""
        try:
            from pymilvus import Collection
            
            collection = Collection(self.collection_name)
            
            data = {
                "id": [kp.id for kp in knowledge_points],
                "subject_id": [kp.metadata.get("subject", "") for kp in knowledge_points],
                "title": [kp.title for kp in knowledge_points],
                "content": [kp.content for kp in knowledge_points],
                "chapter_id": [kp.chapter for kp in knowledge_points],
                "tags": [",".join(kp.tags) for kp in knowledge_points],
                "embedding": [kp.embedding for kp in knowledge_points if kp.embedding],
            }
            
            collection.insert(data)
            collection.flush()
            
            logger.info(f"Inserted {len(knowledge_points)} knowledge points to Milvus")
        
        except Exception as e:
            logger.warning(f"Milvus insert failed: {e}")
    
    async def search(
        self,
        query_embedding: list[float],
        subject_id: Optional[str] = None,
        top_k: int = 5
    ) -> list[dict]:
        """语义搜索"""
        try:
            from pymilvus import Collection
            
            collection = Collection(self.collection_name)
            collection.load()
            
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=f"subject_id == '{subject_id}'" if subject_id else None,
                output_fields=["id", "title", "content", "chapter_id", "tags"]
            )
            
            hits = []
            for hit in results[0]:
                hits.append({
                    "id": hit.entity.get("id"),
                    "title": hit.entity.get("title"),
                    "content": hit.entity.get("content"),
                    "chapter_id": hit.entity.get("chapter_id"),
                    "tags": hit.entity.get("tags"),
                    "score": hit.score
                })
            
            return hits
        
        except Exception as e:
            logger.warning(f"Milvus search failed: {e}")
            return []


class TextbookParser:
    """
    教材智能解析器（主类）
    
    整合 PDF 提取、结构识别、知识点提取、向量化的完整流程
    """
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.structure_recognizer = StructureRecognizer()
        self.knowledge_extractor = KnowledgeExtractor()
        self.embedding_model = None
        if settings.OPENAI_API_KEY:
            self.embedding_model = OpenAIEmbeddings(
                model=settings.OPENAI_EMBEDDING_MODEL,
                api_key=settings.OPENAI_API_KEY
            )
        self.vector_store = VectorStore()
    
    async def parse(
        self,
        file_path: str,
        subject_id: str,
        publisher: str = "",
        grade: str = ""
    ) -> ParseResult:
        """
        解析教材完整流程
        
        Args:
            file_path: PDF 文件路径
            subject_id: 学科 ID
            publisher: 出版社
            grade: 年级
            
        Returns:
            解析结果
        """
        result = ParseResult()
        
        try:
            # 1. PDF 文本提取
            logger.info(f"开始解析教材: {file_path}")
            raw_text = self.pdf_extractor.extract(file_path)
            
            if not raw_text:
                result.error_message = "PDF 文本提取失败，文件可能为空或格式不支持"
                return result
            
            # 2. 结构识别
            logger.info("识别文档结构...")
            structure = self.structure_recognizer.recognize(raw_text)
            structure.title = self.pdf_extractor.extract_with_metadata(file_path).get("title", "")
            structure.publisher = publisher
            structure.grade = grade
            result.structure = structure
            
            # 3. 知识点提取
            logger.info("提取知识点...")
            all_knowledge_points = []
            
            # 遍历所有二级章节进行提取
            sections_to_process = self._get_leaf_sections(structure.sections)
            
            for section in sections_to_process:
                if len(section.content) < 50:
                    continue
                
                kps = await self.knowledge_extractor.extract(
                    content=section.content,
                    subject=subject_id,
                    section_info={"title": section.title, "level": section.level}
                )
                all_knowledge_points.extend(kps)
            
            # 4. 向量化
            logger.info("生成向量...")
            for kp in all_knowledge_points:
                kp.embedding = await self.embedding_model.aembed_query(kp.content)
            
            # 5. 存储到向量库
            logger.info("存储到向量知识库...")
            await self.vector_store.insert(all_knowledge_points)
            
            # 6. 构建知识图谱关系
            knowledge_graph = self._build_knowledge_graph(all_knowledge_points)
            
            # 7. 组装结果
            result.success = True
            result.knowledge_points = all_knowledge_points
            result.knowledge_graph = knowledge_graph
            
            logger.info(
                f"教材解析完成: {len(all_knowledge_points)} 个知识点, "
                f"{len(sections_to_process)} 个章节"
            )
        
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"教材解析失败: {e}")
        
        return result
    
    def _get_leaf_sections(self, sections: list[TextSection]) -> list[TextSection]:
        """获取叶子章节（用于知识提取）"""
        leaves = []
        
        def traverse(section):
            if not section.children:
                leaves.append(section)
            else:
                for child in section.children:
                    traverse(child)
        
        for section in sections:
            traverse(section)
        
        return leaves
    
    def _build_knowledge_graph(self, kps: list[ExtractedKnowledgePoint]) -> dict:
        """构建知识点关联图"""
        graph = {
            "nodes": [],
            "edges": []
        }
        
        # 添加节点
        for kp in kps:
            graph["nodes"].append({
                "id": kp.id,
                "label": kp.title,
                "type": "knowledge_point",
                "difficulty": kp.difficulty,
                "chapter": kp.chapter
            })
        
        # 添加边（基于规则）
        for i, kp in enumerate(kps):
            # 同一章节内的前序关系
            if i > 0 and kp.chapter == kps[i-1].chapter:
                graph["edges"].append({
                    "source": kps[i-1].id,
                    "target": kp.id,
                    "type": "sequence"
                })
            
            # 相似标签的关联关系
            for j, other_kp in enumerate(kps):
                if i != j and set(kp.tags) & set(other_kp.tags):
                    graph["edges"].append({
                        "source": kp.id,
                        "target": other_kp.id,
                        "type": "related"
                    })
        
        return graph


# 单例
_textbook_parser: Optional[TextbookParser] = None


def get_textbook_parser() -> TextbookParser:
    """获取教材解析器单例"""
    global _textbook_parser
    if _textbook_parser is None:
        _textbook_parser = TextbookParser()
    return _textbook_parser
