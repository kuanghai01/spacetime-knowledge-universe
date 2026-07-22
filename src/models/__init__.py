"""
数据模型包
"""
from src.models.base import Base
from src.models.user import User, UserSubjectProgress, UserCurrency, Achievement, UserAchievement
from src.models.subject import Subject, Textbook, KnowledgePoint, StudyRecord
from src.models.gamification import Task, UserTask, UserCompanion, CheckinRecord

__all__ = [
    "Base",
    # User models
    "User",
    "UserSubjectProgress", 
    "UserCurrency",
    "Achievement",
    "UserAchievement",
    # Subject models
    "Subject",
    "Textbook",
    "KnowledgePoint",
    "StudyRecord",
    # Gamification models
    "Task",
    "UserTask",
    "UserCompanion",
    "CheckinRecord",
]
