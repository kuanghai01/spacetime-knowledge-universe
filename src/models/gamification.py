"""
数据模型 - 游戏化系统
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from src.models.base import Base


class Task(Base):
    """任务定义"""
    __tablename__ = "tasks"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    subject_id = Column(String(50), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # daily, weekly, chapter, cross_subject
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(Integer, default=1)
    reward_exp = Column(Integer, default=0)
    reward_currency = Column(JSON, default=dict)
    conditions = Column(JSON, default=dict)  # 完成条件
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserTask(Base):
    """用户任务进度"""
    __tablename__ = "user_tasks"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    task_id = Column(PG_UUID(as_uuid=True), nullable=False)
    status = Column(String(20), default='pending')  # pending, in_progress, completed
    progress = Column(JSON, default=dict)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserCompanion(Base):
    """用户学伴/宠物"""
    __tablename__ = "user_companions"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    companion_type = Column(String(50), nullable=False)  # scholar_cat, wizard_owl
    name = Column(String(100), nullable=True)
    level = Column(Integer, default=1)
    exp = Column(BigInteger, default=0)
    mood = Column(Integer, default=100)  # 0-100
    appearance = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CheckinRecord(Base):
    """签到记录"""
    __tablename__ = "checkin_records"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    checkin_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    streak_days = Column(Integer, default=1)  # 连续签到天数
    exp_gained = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Pydantic 模型
class TaskResponse(BaseModel):
    id: UUID
    subject_id: str
    type: str
    title: str
    description: Optional[str]
    difficulty: int
    reward_exp: int
    reward_currency: dict


class UserTaskResponse(BaseModel):
    id: UUID
    task_id: UUID
    status: str
    progress: dict
    completed_at: Optional[datetime]


class DailyTasksResponse(BaseModel):
    daily_tasks: list[UserTaskResponse]
    chapter_tasks: list[UserTaskResponse]
    total_reward_exp: int


class CompanionResponse(BaseModel):
    id: UUID
    companion_type: str
    name: Optional[str]
    level: int
    exp: int
    mood: int
    appearance: dict


class CheckinResponse(BaseModel):
    success: bool
    streak_days: int
    exp_gained: int
    message: str


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    username: str
    level: int
    exp: int
    avatar_url: Optional[str]


class LeaderboardResponse(BaseModel):
    type: str  # daily, weekly, all_time, subject_xxx
    entries: list[LeaderboardEntry]
    my_rank: Optional[int]
