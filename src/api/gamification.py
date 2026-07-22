"""
API 路由 - 游戏化相关
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import date
import logging

from src.core.gamification.engine import get_gamification_engine
from src.models.gamification import (
    DailyTasksResponse,
    CompanionResponse,
    CheckinResponse,
    LeaderboardResponse,
)
from src.api.users import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gamification", tags=["游戏化"])


@router.post("/checkin", response_model=CheckinResponse)
async def checkin(current_user: dict = Depends(get_current_user)):
    """每日签到"""
    engine = get_gamification_engine()
    
    # 实际查询上次签到时间
    last_checkin = None  # 从数据库获取
    
    result = await engine.process_checkin(
        user_id=current_user["id"],
        last_checkin_date=last_checkin
    )
    
    return CheckinResponse(**result)


@router.get("/tasks/daily")
async def get_daily_tasks(current_user: dict = Depends(get_current_user)):
    """获取每日任务"""
    return {
        "daily_tasks": [
            {
                "id": "task_1",
                "title": "学习3个知识点",
                "description": "在任何学科中学习3个新知识点",
                "progress": 1,
                "target": 3,
                "reward_exp": 30,
                "reward_currency": {"knowledge_coin": 10}
            },
            {
                "id": "task_2",
                "title": "完成一次练习",
                "description": "完成任意学科的练习题",
                "progress": 0,
                "target": 1,
                "reward_exp": 20,
                "reward_currency": {"knowledge_coin": 5}
            },
            {
                "id": "task_3",
                "title": "帮助同学",
                "description": "在讨论区回答一个问题",
                "progress": 0,
                "target": 1,
                "reward_exp": 25,
                "reward_currency": {"knowledge_coin": 8}
            }
        ],
        "reset_time": "明天 00:00"
    }


@router.get("/tasks/chapter/{chapter_id}")
async def get_chapter_tasks(chapter_id: str, current_user: dict = Depends(get_current_user)):
    """获取章节任务"""
    return {
        "chapter_id": chapter_id,
        "tasks": [
            {
                "id": "ch_task_1",
                "title": "了解秦始皇",
                "description": "学习秦始皇统一六国的相关内容",
                "type": "knowledge",
                "reward_exp": 50,
                "locked": False
            },
            {
                "id": "ch_task_2",
                "title": "历史小测验",
                "description": "完成章节测试，正确率达到80%",
                "type": "quiz",
                "reward_exp": 100,
                "locked": False
            },
            {
                "id": "ch_task_3",
                "title": "时空探险家",
                "description": "完成章节内的互动任务",
                "type": "interactive",
                "reward_exp": 80,
                "locked": True,
                "unlock_condition": "完成前两个任务"
            }
        ]
    }


@router.get("/leaderboard/{leaderboard_type}")
async def get_leaderboard(
    leaderboard_type: str,  # daily, weekly, all_time
    subject_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """获取排行榜"""
    engine = get_gamification_engine()
    
    entries = await engine.leaderboard_service.get_leaderboard(
        leaderboard_type=leaderboard_type,
        subject_id=subject_id
    )
    
    my_rank = await engine.leaderboard_service.get_user_rank(
        user_id=current_user["id"],
        leaderboard_type=leaderboard_type
    )
    
    return {
        "type": leaderboard_type,
        "subject_id": subject_id,
        "entries": entries,
        "my_rank": my_rank
    }


@router.get("/companion")
async def get_companion(current_user: dict = Depends(get_current_user)):
    """获取学伴状态"""
    return {
        "id": "comp_1",
        "type": "scholar_cat",
        "name": "小学喵",
        "level": 3,
        "exp": 450,
        "next_level_exp": 600,
        "mood": 85,
        "appearance": {
            "hat": "scholar_cap",
            "accessory": "glasses"
        },
        "message": "喵~今天也要加油学习哦！",
        "abilities": [
            {"id": "exp_boost", "name": "经验加成", "level": 2, "effect": "+10% 经验"}
        ]
    }


@router.post("/companion/feed")
async def feed_companion(current_user: dict = Depends(get_current_user)):
    """喂养学伴"""
    return {
        "success": True,
        "mood_increased": 10,
        "new_mood": 95,
        "message": "小学喵很开心！"
    }


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    """获取学习统计"""
    return {
        "total_study_time_minutes": 1250,
        "total_knowledge_points": 45,
        "total_quizzes": 12,
        "average_accuracy": 82,
        "strongest_subject": "history",
        "weakest_subject": None,
        "weekly_activity": [
            {"date": "2026-07-15", "minutes": 45},
            {"date": "2026-07-16", "minutes": 30},
            {"date": "2026-07-17", "minutes": 60},
            {"date": "2026-07-18", "minutes": 0},
            {"date": "2026-07-19", "minutes": 20},
            {"date": "2026-07-20", "minutes": 45},
            {"date": "2026-07-21", "minutes": 35},
        ]
    }
