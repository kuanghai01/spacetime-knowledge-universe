"""
用户资产服务

管理:
1. 用户货币（铜币/银币/金币）
2. 用户等级与经验
3. 用户宠物/伙伴系统
4. 用户背包（购买的物品）
5. 资产变动历史
"""
import logging
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CurrencyType(str, Enum):
    """货币类型"""
    COPPER = "copper"      # 铜币（基础货币）
    SILVER = "silver"      # 银币（100铜币=1银币）
    GOLD = "gold"          # 金币（100银币=1金币）


@dataclass
class UserAsset:
    """用户资产快照"""
    user_id: str
    copper: int = 0
    silver: int = 0
    gold: int = 0
    exp: int = 0
    level: int = 1
    total_study_minutes: int = 0
    total_questions_answered: int = 0

    @property
    def total_copper_value(self) -> int:
        """折合总铜币"""
        return self.copper + self.silver * 100 + self.gold * 10000

    @property
    def next_level_exp(self) -> int:
        """下一级所需经验"""
        return self.level * self.level * 100

    @property
    def current_level_progress(self) -> float:
        """当前等级进度 0.0~1.0"""
        current_level_base = (self.level - 1) * (self.level - 1) * 100 if self.level > 1 else 0
        next_level_base = self.next_level_exp
        if next_level_base <= current_level_base:
            return 1.0
        progress = (self.exp - current_level_base) / (next_level_base - current_level_base)
        return min(max(progress, 0.0), 1.0)


@dataclass
class AssetTransaction:
    """资产变动记录"""
    user_id: str
    currency: CurrencyType
    amount: int
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    balance_after: int = 0


class UserAssetService:
    """用户资产服务（单例）"""

    _instance: Optional["UserAssetService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._assets: dict[str, UserAsset] = {}
            self._transactions: dict[str, list[AssetTransaction]] = {}
            self._inventory: dict[str, list[str]] = {}
            self._equipped: dict[str, Optional[str]] = {}
            self._initialized = True

    def reset(self):
        """重置所有数据（测试用）"""
        self._assets.clear()
        self._transactions.clear()
        self._inventory.clear()
        self._equipped.clear()

    def get_or_create_asset(self, user_id: str) -> UserAsset:
        """获取或创建用户资产"""
        if user_id not in self._assets:
            self._assets[user_id] = UserAsset(user_id=user_id)
            self._transactions[user_id] = []
            self._inventory[user_id] = []
            self._equipped[user_id] = None
        return self._assets[user_id]

    def get_asset(self, user_id: str) -> Optional[UserAsset]:
        """获取用户资产"""
        return self._assets.get(user_id)

    def add_currency(self, user_id: str, currency: CurrencyType, amount: int, reason: str = "") -> UserAsset:
        """增加货币"""
        asset = self.get_or_create_asset(user_id)
        if currency == CurrencyType.COPPER:
            asset.copper += amount
            balance = asset.copper
        elif currency == CurrencyType.SILVER:
            asset.silver += amount
            balance = asset.silver
        elif currency == CurrencyType.GOLD:
            asset.gold += amount
            balance = asset.gold
        else:
            raise ValueError(f"未知货币类型: {currency}")

        # 记录交易
        tx = AssetTransaction(
            user_id=user_id,
            currency=currency,
            amount=amount,
            reason=reason,
            balance_after=balance,
        )
        self._transactions[user_id].append(tx)

        # 自动兑换
        self._auto_exchange(user_id)
        return self._assets[user_id]

    def spend_currency(self, user_id: str, currency: CurrencyType, amount: int, reason: str = "") -> bool:
        """消费货币"""
        asset = self.get_or_create_asset(user_id)

        if currency == CurrencyType.COPPER:
            if asset.copper < amount:
                return False
            asset.copper -= amount
        elif currency == CurrencyType.SILVER:
            if asset.silver < amount:
                return False
            asset.silver -= amount
        elif currency == CurrencyType.GOLD:
            if asset.gold < amount:
                return False
            asset.gold -= amount

        tx = AssetTransaction(
            user_id=user_id,
            currency=currency,
            amount=-amount,
            reason=reason,
            balance_after=getattr(asset, currency.value),
        )
        self._transactions[user_id].append(tx)
        return True

    def spend_with_auto_exchange(self, user_id: str, total_copper: int, reason: str = "") -> bool:
        """
        智能支付（自动兑换大面额货币）

        优先使用小面额，不足时自动兑换大面额
        """
        asset = self.get_or_create_asset(user_id)
        if asset.total_copper_value < total_copper:
            return False

        remaining = total_copper

        # 先用铜币
        use_copper = min(asset.copper, remaining)
        remaining -= use_copper
        asset.copper -= use_copper

        # 再用银币
        if remaining > 0:
            use_silver = min(asset.silver, remaining // 100)
            remaining -= use_silver * 100
            asset.silver -= use_silver

        # 最后用金币
        if remaining > 0:
            use_gold = (remaining + 9999) // 10000  # 向上取整
            remaining -= use_gold * 10000
            asset.gold -= use_gold

        # 多余的找零
        if remaining < 0:
            asset.copper += abs(remaining)
            self._auto_exchange(user_id)

        tx = AssetTransaction(
            user_id=user_id,
            currency=CurrencyType.COPPER,
            amount=-total_copper,
            reason=f"[智能支付] {reason}",
            balance_after=asset.total_copper_value,
        )
        self._transactions[user_id].append(tx)
        return True

    def add_experience(self, user_id: str, amount: int, reason: str = "") -> dict:
        """增加经验值（自动升级检查）"""
        asset = self.get_or_create_asset(user_id)
        asset.exp += amount

        # 检查升级
        level_up = False
        levels_gained = 0
        while True:
            next_level_exp = (asset.level + 1) * (asset.level + 1) * 100
            if asset.exp >= next_level_exp:
                asset.level += 1
                level_up = True
                levels_gained += 1
            else:
                break

        # 升级奖励
        if level_up:
            bonus_copper = levels_gained * 50
            self.add_currency(user_id, CurrencyType.COPPER, bonus_copper,
                            f"🎉 升级到 Lv.{asset.level} 奖励")

        return {
            "exp_gained": amount,
            "level_up": level_up,
            "levels_gained": levels_gained,
            "new_level": asset.level,
            "current_exp": asset.exp,
            "next_level_exp": asset.next_level_exp,
            "progress": asset.current_level_progress,
        }

    def purchase_item(self, user_id: str, item_id: str, cost: int, reason: str = "") -> bool:
        """购买物品"""
        if not self.spend_with_auto_exchange(user_id, cost, reason or f"购买 {item_id}"):
            return False

        if user_id not in self._inventory:
            self._inventory[user_id] = []
        self._inventory[user_id].append(item_id)
        return True

    def equip_companion(self, user_id: str, companion_id: str) -> bool:
        """装备宠物"""
        if companion_id not in self._inventory.get(user_id, []):
            return False
        self._equipped[user_id] = companion_id
        return True

    def get_inventory(self, user_id: str) -> list[str]:
        """获取用户背包"""
        return self._inventory.get(user_id, [])

    def get_equipped(self, user_id: str) -> Optional[str]:
        """获取当前装备的宠物"""
        return self._equipped.get(user_id)

    def get_transactions(self, user_id: str, limit: int = 20) -> list[AssetTransaction]:
        """获取资产变动历史"""
        return self._transactions.get(user_id, [])[-limit:]

    def get_level_title(self, level: int) -> str:
        """获取等级称号"""
        titles = {
            1: "初学者",
            5: "小学生",
            10: "中学生",
            15: "大学生",
            20: "研究生",
            30: "学者",
            40: "教授",
            50: "大师",
            60: "宗师",
            80: "贤者",
            100: "时空守护者",
        }
        current_title = "初学者"
        for lvl, title in sorted(titles.items()):
            if level >= lvl:
                current_title = title
        return current_title

    def _auto_exchange(self, user_id: str):
        """自动兑换货币（100铜=1银，100银=1金）"""
        asset = self._assets[user_id]

        # 升级兑换：铜币→银币，银币→金币
        if asset.copper >= 100:
            asset.silver += asset.copper // 100
            asset.copper %= 100
        if asset.silver >= 100:
            asset.gold += asset.silver // 100
            asset.silver %= 100


def get_user_asset_service() -> UserAssetService:
    """获取用户资产服务实例"""
    return UserAssetService()
