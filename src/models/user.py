"""
数据模型 - 用户与资产
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from src.models.base import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    hashed_password = Column(String(200), nullable=False)
    avatar_url = Column(Text, nullable=True)
    level = Column(Integer, default=1)
    exp = Column(BigInteger, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserSubjectProgress(Base):
    """用户学科进度"""
    __tablename__ = "user_subject_progress"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    subject_id = Column(String(50), nullable=False, index=True)
    chapter_id = Column(String(100), nullable=True)
    mastery_level = Column(Integer, default=0)  # 0-100
    total_exp = Column(BigInteger, default=0)
    last_study_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class UserCurrency(Base):
    """用户货币"""
    __tablename__ = "user_currency"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    currency_type = Column(String(50), nullable=False)  # knowledge_coin, energy, gem
    amount = Column(BigInteger, default=0)


class Achievement(Base):
    """成就定义"""
    __tablename__ = "achievements"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon_url = Column(Text, nullable=True)
    condition_type = Column(String(50), nullable=False)  # study_hours, streak_days, mastery_level
    condition_value = Column(Integer, nullable=False)
    reward_exp = Column(Integer, default=0)
    reward_currency = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)


class UserAchievement(Base):
    """用户成就"""
    __tablename__ = "user_achievements"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    achievement_id = Column(PG_UUID(as_uuid=True), nullable=False)
    unlocked_at = Column(DateTime(timezone=True), server_default=func.now())


# Pydantic 模型 (API 传输对象)
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: Optional[str]
    avatar_url: Optional[str]
    level: int
    exp: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserProgressResponse(BaseModel):
    subject_id: str
    chapter_id: Optional[str]
    mastery_level: int
    total_exp: int
    last_study_at: Optional[datetime]


class UserDashboardResponse(BaseModel):
    user: UserResponse
    progress: list[UserProgressResponse]
    achievements_count: int
    currency: dict[str, int]
