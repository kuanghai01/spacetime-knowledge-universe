"""
测试 - 游戏化引擎
"""
import pytest
from datetime import date, timedelta

from src.core.gamification.engine import (
    ExpCalculator,
    AchievementSystem,
    CheckinSystem,
    GamificationEngine,
)


class TestExpCalculator:
    """经验值计算器测试"""
    
    @pytest.fixture
    def calculator(self):
        return ExpCalculator()
    
    def test_base_exp_calculation(self, calculator):
        """测试基础经验值计算"""
        result = calculator.calculate(
            activity_type="quiz",
            difficulty=1
        )
        assert result.base_exp == 10  # BASE_EXP_PER_KNOWLEDGE * difficulty
    
    def test_difficulty_multiplier(self, calculator):
        """测试难度加成"""
        result = calculator.calculate(
            activity_type="quiz",
            difficulty=3
        )
        assert result.base_exp == 30  # 10 * 3
    
    def test_streak_bonus(self, calculator):
        """测试连续学习加成"""
        result = calculator.calculate(
            activity_type="quiz",
            difficulty=1,
            consecutive_days=5
        )
        assert "streak" in result.bonuses
        assert result.total_exp > result.base_exp
    
    def test_first_mastery_bonus(self, calculator):
        """测试首次掌握加成"""
        result = calculator.calculate(
            activity_type="quiz",
            difficulty=1,
            is_first_mastery=True
        )
        assert "first_mastery" in result.bonuses
    
    def test_perfect_answer_bonus(self, calculator):
        """测试完美答题加成"""
        result = calculator.calculate(
            activity_type="quiz",
            difficulty=1,
            accuracy=1.0
        )
        assert "perfect" in result.bonuses
    
    def test_level_calculation(self, calculator):
        """测试等级计算"""
        assert calculator.get_level_from_exp(0) == 1
        assert calculator.get_level_from_exp(100) == 2
        assert calculator.get_level_from_exp(500) == 3
        assert calculator.get_level_from_exp(5000) >= 10


class TestAchievementSystem:
    """成就系统测试"""
    
    @pytest.fixture
    def system(self):
        return AchievementSystem()
    
    def test_check_study_count_achievement(self, system):
        """测试学习次数成就"""
        user_stats = {"study_count": 1}
        unlocked = system.check_achievements(user_stats, set())
        
        achievement_ids = [a["id"] for a in unlocked]
        assert "first_step" in achievement_ids
    
    def test_check_streak_achievement(self, system):
        """测试连续学习成就"""
        user_stats = {"streak_days": 7}
        unlocked = system.check_achievements(user_stats, set())
        
        achievement_ids = [a["id"] for a in unlocked]
        assert "streak_7" in achievement_ids
    
    def test_skip_already_unlocked(self, system):
        """测试跳过已解锁成就"""
        user_stats = {"study_count": 10}
        unlocked = system.check_achievements(user_stats, {"first_step"})
        
        achievement_ids = [a["id"] for a in unlocked]
        assert "first_step" not in achievement_ids


class TestCheckinSystem:
    """签到系统测试"""
    
    @pytest.fixture
    def system(self):
        return CheckinSystem()
    
    def test_first_day_reward(self, system):
        """测试第一天奖励"""
        reward = system.calculate_checkin_reward(1)
        assert reward == 10
    
    def test_seventh_day_reward(self, system):
        """测试第七天奖励"""
        reward = system.calculate_checkin_reward(7)
        assert reward == 50  # 第七天额外奖励
    
    def test_should_reset_streak(self, system):
        """测试连续签到重置"""
        # 从未签到
        assert system.should_reset_streak(None) is True
        
        # 昨天签到了
        yesterday = date.today() - timedelta(days=1)
        assert system.should_reset_streak(yesterday) is False
        
        # 两天前签到了
        two_days_ago = date.today() - timedelta(days=2)
        assert system.should_reset_streak(two_days_ago) is True


class TestGamificationEngine:
    """游戏化引擎测试"""
    
    @pytest.fixture
    def engine(self):
        return GamificationEngine()
    
    @pytest.mark.asyncio
    async def test_process_study_activity(self, engine):
        """测试处理学习活动"""
        activity = {
            "type": "quiz",
            "difficulty": 2,
            "accuracy": 0.8,
            "consecutive_days": 3,
            "time_spent": 300
        }
        
        result = await engine.process_study_activity("test_user", activity)
        
        assert "exp_gained" in result
        assert result["exp_gained"] > 0
        assert "exp_breakdown" in result
    
    @pytest.mark.asyncio
    async def test_process_checkin(self, engine):
        """测试签到处理"""
        result = await engine.process_checkin("test_user", None)
        
        assert result["success"] is True
        assert result["streak_days"] == 1
        assert result["exp_gained"] > 0
