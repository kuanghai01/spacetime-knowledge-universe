"""
纯 Pydantic 模型（无 SQLAlchemy 依赖，供 Render 精简版使用）
"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class SubjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: bool = True


class ChapterResponse(BaseModel):
    chapter_id: str
    title: str
    section_count: int
    mastery_level: int = 0


class KnowledgePointResponse(BaseModel):
    id: UUID
    subject_id: str
    chapter_id: Optional[str] = None
    title: str
    content: Optional[str] = None
    difficulty: int = 1
    tags: list[str] = []


class TextbookResponse(BaseModel):
    id: UUID
    subject_id: str
    publisher: str
    grade: str
    version_year: Optional[int] = None
    status: str = "processing"


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
