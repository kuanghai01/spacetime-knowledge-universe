"""
数据模型 - 学科与知识
"""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Text, Float
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.models.base import Base


class Subject(Base):
    """学科配置"""
    __tablename__ = "subjects"
    
    id = Column(String(50), primary_key=True)  # 'history', 'physics'
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon_url = Column(Text, nullable=True)
    agent_config = Column(JSON, default=dict)  # Agent 配置
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Textbook(Base):
    """教材版本"""
    __tablename__ = "textbooks"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    subject_id = Column(String(50), nullable=False, index=True)
    publisher = Column(String(100))  # '人教版', '苏教版'
    grade = Column(String(50))  # '七年级', '八年级', '九年级'
    version_year = Column(Integer)
    file_path = Column(Text, nullable=True)
    parsed_data = Column(JSON, default=dict)
    status = Column(String(20), default='pending')  # pending, parsing, ready, error
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KnowledgePoint(Base):
    """知识点"""
    __tablename__ = "knowledge_points"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    subject_id = Column(String(50), nullable=False, index=True)
    textbook_id = Column(PG_UUID(as_uuid=True), nullable=True)
    chapter_id = Column(String(100), nullable=True, index=True)
    section_id = Column(String(100), nullable=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    difficulty = Column(Integer, default=1)  # 1-5
    tags = Column(ARRAY(String), default=list)
    # embedding 存储在 Milvus 中，通过 id 关联
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StudyRecord(Base):
    """学习记录"""
    __tablename__ = "study_records"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    subject_id = Column(String(50), nullable=False, index=True)
    knowledge_point_id = Column(PG_UUID(as_uuid=True), nullable=True)
    activity_type = Column(String(50), nullable=False)  # quiz, reading, experiment, discussion
    score = Column(Integer, nullable=True)  # 正确率或完成度 0-100
    time_spent = Column(Integer, nullable=True)  # 秒
    exp_gained = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Pydantic 模型
class SubjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    icon_url: Optional[str]
    is_active: bool


class ChapterResponse(BaseModel):
    chapter_id: str
    title: str
    section_count: int
    mastery_level: int  # 用户对该章节的掌握度


class KnowledgePointResponse(BaseModel):
    id: UUID
    subject_id: str
    chapter_id: Optional[str]
    title: str
    content: Optional[str]
    difficulty: int
    tags: list[str]


class TextbookResponse(BaseModel):
    id: UUID
    subject_id: str
    publisher: str
    grade: str
    version_year: Optional[int]
    status: str


class TextbookUploadRequest(BaseModel):
    subject_id: str
    publisher: str
    grade: str
    version_year: Optional[int] = None


class StudyRecordCreate(BaseModel):
    subject_id: str
    knowledge_point_id: Optional[UUID] = None
    activity_type: str
    score: Optional[int] = None
    time_spent: Optional[int] = None
