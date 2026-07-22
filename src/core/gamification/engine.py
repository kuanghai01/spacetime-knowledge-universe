"""
游戏化引擎

负责:
1. 经验值计算与等级系统
2. 成就系统
3. 任务管理
4. 签到与连续学习
5. 排行榜
"""
import logging
from typing import Optional
from datetime import datetime, date, timedelta
from dataclasses import dataclass

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ExpResult:
    """经验值计算结果"""
    base_exp: int
    bonuses: dict[str, float]
    total_exp: int
    level_up: bool = False
    new_level: int = 0


class ExpCalculator:
    """经验值计算器"""
    
    # 等级经验需求表
    LEVEL_EXP_TABLE = {
        1: 0,
        2: 100,
        3: 300,
        4: 600,
        5: 1000,
        6: 1500,
        7: 2100,
        8: 2800,
        9: 3600,
        10: 4500,
    }
    
    def get_exp_for_level(self, level: int) -> int:
        """获取升级所需经验"""
        return self.LEVEL_EXP_TABLE.get(level, level * 500)
    
    def get_level_from_exp(self, total_exp: int) -> int:
        """根据总经验计算等级"""
        level = 1
        for lvl, exp_needed in sorted(self.LEVEL_EXP_TABLE.items(), reverse=True):
            if total_exp >= exp_needed:
                level = lvl
                break
        return level
    
    def calculate(
        self,
        activity_type: str,
        difficulty: int = 1,
        accuracy: float = 1.0,
        consecutive_days: int = 1,
        is_first_mastery: bool = False,
        cross_subject: bool = False,
        time_spent_seconds: int = 0
    ) -> ExpResult:
        """
        计算经验值
        
        Args:
            activity_type: 活动类型 (quiz, reading, experiment, discussion)
            difficulty: 难度 1-5
            accuracy: 正确率 0-1
            consecutive_days: 连续学习天数
            is_first_mastery: 是否首次掌握
            cross_subject: 是否跨学科
            time_spent_seconds: 学习时长（秒）
        """
        # 基础经验
        base_exp = settings.BASE_EXP_PER_KNOWLEDGE * difficulty
        
        # 加成计算
        bonuses = {}
        multiplier = 1.0
        
        # 连续学习加成
        streak_bonus = min(consecutive_days * 0.1, settings.MAX_STREAK_BONUS)
        if streak_bonus > 0:
            bonuses["streak"] = streak_bonus
            multiplier += streak_bonus
        
        # 首次掌握加成
        if is_first_mastery:
            bonuses["first_mastery"] = settings.FIRST_MASTERY_BONUS - 1
            multiplier *= settings.FIRST_MASTERY_BONUS
        
        # 完美答题加成
        if accuracy >= 1.0:
            bonuses["perfect"] = settings.PERFECT_ANSWER_BONUS - 1
            multiplier *= settings.PERFECT_ANSWER_BONUS
        
        # 跨学科加成
        if cross_subject:
            bonuses["cross_subject"] = settings.CROSS_SUBJECT_BONUS - 1
            multiplier *= settings.CROSS_SUBJECT_BONUS
        
        # 时长加成（超过5分钟有额外奖励）
        if time_spent_seconds > 300:
            time_bonus = min((time_spent_seconds - 300) / 600, 0.5)
            bonuses["time"] = time_bonus
            multiplier += time_bonus
        
        total_exp = int(base_exp * multiplier)
        
        return ExpResult(
            base_exp=base_exp,
            bonuses=bonuses,
            total_exp=total_exp
        )


class AchievementSystem:
    """成就系统"""
    
    # 预定义成就
    ACHIEVEMENTS = [
        # 学习类
        {"id": "first_step", "name": "第一步", "desc": "完成第一次学习", "condition": {"type": "study_count", "value": 1}},
        {"id": "scholar_10", "name": "小学者", "desc": "学习10个知识点", "condition": {"type": "knowledge_count", "value": 10}},
        {"id": "scholar_100", "name": "大学者", "desc": "学习100个知识点", "condition": {"type": "knowledge_count", "value": 100}},
        
        # 连续学习
        {"id": "streak_3", "name": "三日坚持", "desc": "连续学习3天", "condition": {"type": "streak_days", "value": 3}},
        {"id": "streak_7", "name": "一周达人", "desc": "连续学习7天", "condition": {"type": "streak_days", "value": 7}},
        {"id": "streak_30", "name": "月度之星", "desc": "连续学习30天", "condition": {"type": "streak_days", "value": 30}},
        
        # 学科类
        {"id": "history_master", "name": "历史通", "desc": "历史掌握度达到80%", "condition": {"type": "subject_mastery", "subject": "history", "value": 80}},
        {"id": "physics_master", "name": "物理达人", "desc": "物理掌握度达到80%", "condition": {"type": "subject_mastery", "subject": "physics", "value": 80}},
        
        # 跨学科
        {"id": "polymath", "name": "博学多才", "desc": "在3个学科达到50%掌握度", "condition": {"type": "multi_subject", "count": 3, "value": 50}},
    ]
    
    def check_achievements(
        self,
        user_stats: dict,
        unlocked_ids: set[str]
    ) -> list[dict]:
        """
        检查可解锁的成就
        
        Args:
            user_stats: 用户统计数据
            unlocked_ids: 已解锁的成就 ID
            
        Returns:
            新解锁的成就列表
        """
        new_achievements = []
        
        for achievement in self.ACHIEVEMENTS:
            if achievement["id"] in unlocked_ids:
                continue
            
            condition = achievement["condition"]
            cond_type = condition["type"]
            
            unlocked = False
            
            if cond_type == "study_count":
                unlocked = user_stats.get("study_count", 0) >= condition["value"]
            elif cond_type == "knowledge_count":
                unlocked = user_stats.get("knowledge_count", 0) >= condition["value"]
            elif cond_type == "streak_days":
                unlocked = user_stats.get("streak_days", 0) >= condition["value"]
            elif cond_type == "subject_mastery":
                subject = condition["subject"]
                mastery = user_stats.get("subject_mastery", {}).get(subject, 0)
                unlocked = mastery >= condition["value"]
            elif cond_type == "multi_subject":
                mastery_dict = user_stats.get("subject_mastery", {})
                count = sum(1 for m in mastery_dict.values() if m >= condition["value"])
                unlocked = count >= condition["count"]
            
            if unlocked:
                new_achievements.append(achievement)
        
        return new_achievements


class CheckinSystem:
    """签到系统"""
    
    # 签到经验奖励
    CHECKIN_REWARDS = {
        1: 10,   # 第1天
        2: 15,
        3: 20,
        4: 25,
        5: 30,
        6: 35,
        7: 50,   # 第7天额外奖励
    }
    
    def calculate_checkin_reward(self, streak_days: int) -> int:
        """计算签到奖励"""
        # 7天一个周期
        day_in_cycle = ((streak_days - 1) % 7) + 1
        return self.CHECKIN_REWARDS.get(day_in_cycle, 10)
    
    def should_reset_streak(self, last_checkin: Optional[date]) -> bool:
        """判断是否应该重置连续签到"""
        if last_checkin is None:
            return True
        
        today = date.today()
        days_diff = (today - last_checkin).days
        
        # 超过1天未签到则重置
        return days_diff > 1


class LeaderboardService:
    """排行榜服务"""
    
    async def get_leaderboard(
        self,
        leaderboard_type: str = "all_time",
        limit: int = 50,
        subject_id: Optional[str] = None
    ) -> list[dict]:
        """
        获取排行榜
        
        Args:
            leaderboard_type: daily, weekly, all_time, subject_{id}
            limit: 返回数量
            subject_id: 学科 ID（学科排行榜）
        """
        # 实际从数据库查询
        # 这里返回示例数据
        return [
            {"rank": 1, "user_id": "user_1", "username": "学霸小明", "level": 10, "exp": 5000},
            {"rank": 2, "user_id": "user_2", "username": "知识达人", "level": 9, "exp": 4200},
            {"rank": 3, "user_id": "user_3", "username": "历史迷", "level": 8, "exp": 3500},
        ]
    
    async def get_user_rank(self, user_id: str, leaderboard_type: str = "all_time") -> int:
        """获取用户排名"""
        # 实际从数据库查询
        return 100


class GamificationEngine:
    """
    游戏化引擎主类
    
    整合所有游戏化功能
    """
    
    def __init__(self):
        self.exp_calculator = ExpCalculator()
        self.achievement_system = AchievementSystem()
        self.checkin_system = CheckinSystem()
        self.leaderboard_service = LeaderboardService()
    
    async def process_study_activity(
        self,
        user_id: str,
        activity: dict
    ) -> dict:
        """
        处理学习活动
        
        Returns:
            包含经验值、成就等信息的结果
        """
        # 1. 计算经验值
        exp_result = self.exp_calculator.calculate(
            activity_type=activity.get("type", "quiz"),
            difficulty=activity.get("difficulty", 1),
            accuracy=activity.get("accuracy", 1.0),
            consecutive_days=activity.get("consecutive_days", 1),
            is_first_mastery=activity.get("is_first_mastery", False),
            cross_subject=activity.get("cross_subject", False),
            time_spent_seconds=activity.get("time_spent", 0)
        )
        
        # 2. 检查成就（需要查询用户数据）
        # new_achievements = self.achievement_system.check_achievements(...)
        
        return {
            "exp_gained": exp_result.total_exp,
            "exp_breakdown": {
                "base": exp_result.base_exp,
                "bonuses": exp_result.bonuses
            },
            "level_up": exp_result.level_up,
            "new_level": exp_result.new_level,
            "new_achievements": []  # 实际从数据库获取
        }
    
    async def process_checkin(self, user_id: str, last_checkin_date: Optional[date]) -> dict:
        """处理签到"""
        today = date.today()
        
        # 判断连续天数
        if self.checkin_system.should_reset_streak(last_checkin_date):
            streak_days = 1
        else:
            streak_days = (today - last_checkin_date).days + 1 if last_checkin_date else 1
        
        # 计算奖励
        exp_reward = self.checkin_system.calculate_checkin_reward(streak_days)
        
        return {
            "success": True,
            "streak_days": streak_days,
            "exp_gained": exp_reward,
            "message": self._get_checkin_message(streak_days)
        }
    
    def _get_checkin_message(self, streak_days: int) -> str:
        """获取签到消息"""
        if streak_days == 1:
            return "新的一天，新的开始！加油！"
        elif streak_days < 7:
            return f"已连续学习 {streak_days} 天，继续保持！"
        elif streak_days == 7:
            return "🎉 一周达成！你是学习达人！"
        else:
            return f"🔥 连续 {streak_days} 天！太厉害了！"


# 单例
_gamification_engine: Optional[GamificationEngine] = None


def get_gamification_engine() -> GamificationEngine:
    """获取游戏化引擎单例"""
    global _gamification_engine
    if _gamification_engine is None:
        _gamification_engine = GamificationEngine()
    return _gamification_engine
