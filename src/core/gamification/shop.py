"""
积分商城系统

商品类型:
- 宠物/伙伴：可爱的学习伙伴，装备后陪伴学习
- 装扮/皮肤：头像框、背景、聊天气泡
- 道具/增益：双倍经验卡、提示卡、跳过卡
- 特权/服务：VIP体验、专属内容解锁
"""
import logging
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.core.gamification.user_asset import CurrencyType, get_user_asset_service

logger = logging.getLogger(__name__)


class ItemCategory(str, Enum):
    """商品分类"""
    COMPANION = "companion"      # 宠物/伙伴
    COSMETIC = "cosmetic"        # 装扮/皮肤
    POWER_UP = "power_up"        # 道具/增益
    PRIVILEGE = "privilege"      # 特权/服务


class ItemRarity(str, Enum):
    """物品稀有度"""
    COMMON = "common"            # 普通（白色）
    UNCOMMON = "uncommon"        # 优秀（绿色）
    RARE = "rare"                # 稀有（蓝色）
    EPIC = "epic"                # 史诗（紫色）
    LEGENDARY = "legendary"      # 传说（橙色）


@dataclass
class ShopItem:
    """商城商品"""
    id: str
    name: str
    description: str
    category: ItemCategory
    rarity: ItemRarity
    price: int                   # 铜币价格
    currency: CurrencyType = CurrencyType.COPPER
    emoji: str = "🎁"
    icon: str = "📦"
    effect: dict = field(default_factory=dict)       # 道具效果
    duration_hours: int = 0     # 限时道具的时长（0=永久）
    limited: bool = False       # 是否限量
    stock: int = -1             # 剩余库存（-1=无限）

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "rarity": self.rarity.value,
            "rarity_color": self._rarity_color(),
            "price": self.price,
            "currency": self.currency.value,
            "emoji": self.emoji,
            "icon": self.icon,
            "effect": self.effect,
            "duration_hours": self.duration_hours,
            "limited": self.limited,
            "stock": self.stock,
        }

    def _rarity_color(self) -> str:
        colors = {
            ItemRarity.COMMON: "#95a5a6",
            ItemRarity.UNCOMMON: "#2ecc71",
            ItemRarity.RARE: "#3498db",
            ItemRarity.EPIC: "#9b59b6",
            ItemRarity.LEGENDARY: "#e67e22",
        }
        return colors.get(self.rarity, "#95a5a6")


class PointsShop:
    """积分商城"""

    def __init__(self):
        self.items: dict[str, ShopItem] = {}
        self._init_default_items()

    def _init_default_items(self):
        """初始化默认商品"""
        default_items = [
            # === 宠物/伙伴 ===
            ShopItem(
                id="companion_dragon",
                name="时光小龙",
                description="🐲 一只会喷火的小龙，陪伴你学习时会随机给予经验加成",
                category=ItemCategory.COMPANION,
                rarity=ItemRarity.RARE,
                price=5000,
                emoji="🐲",
                icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🐲</text></svg>",
                effect={"exp_bonus": 0.1, "special_hint": True},
            ),
            ShopItem(
                id="companion_cat",
                name="知识小猫",
                description="🐱 一只聪明的猫咪，每天第一次学习时额外奖励经验",
                category=ItemCategory.COMPANION,
                rarity=ItemRarity.UNCOMMON,
                price=2000,
                emoji="🐱",
                effect={"daily_first_exp_bonus": 20},
            ),
            ShopItem(
                id="companion_phoenix",
                name="凤凰使者",
                description="🦦 传说中的凤凰，学习时火焰环绕，经验+30%，有概率触发复活（抵消一次错误）",
                category=ItemCategory.COMPANION,
                rarity=ItemRarity.LEGENDARY,
                price=20000,
                emoji="🦦",
                effect={"exp_bonus": 0.3, "revive_chance": 0.05},
            ),
            ShopItem(
                id="companion_panda",
                name="时空熊猫",
                description="🐼 来自时空隧道的熊猫，温和友善，每次答题+5铜币",
                category=ItemCategory.COMPANION,
                rarity=ItemRarity.COMMON,
                price=800,
                emoji="🐼",
                effect={"copper_per_answer": 5},
            ),

            # === 装扮/皮肤 ===
            ShopItem(
                id="cosmetic_golden_frame",
                name="黄金头像框",
                description="👑 黄金打造的头像框，彰显尊贵身份",
                category=ItemCategory.COSMETIC,
                rarity=ItemRarity.EPIC,
                price=3000,
                emoji="👑",
            ),
            ShopItem(
                id="cosmetic_starry_bg",
                name="星空背景",
                description="✨ 动态星空背景，让学习页面充满宇宙感",
                category=ItemCategory.COSMETIC,
                rarity=ItemRarity.RARE,
                price=2500,
                emoji="✨",
            ),
            ShopItem(
                id="cosmetic_dynasty_frame",
                name="王朝边框",
                description="🏛️ 古代王朝风格的头像框，历史感满满",
                category=ItemCategory.COSMETIC,
                rarity=ItemRarity.UNCOMMON,
                price=1000,
                emoji="🏛️",
            ),

            # === 道具/增益 ===
            ShopItem(
                id="powerup_double_exp",
                name="双倍经验卡",
                description="📖 使用后1小时内所有学习经验翻倍",
                category=ItemCategory.POWER_UP,
                rarity=ItemRarity.RARE,
                price=800,
                emoji="📖",
                effect={"exp_multiplier": 2.0},
                duration_hours=1,
            ),
            ShopItem(
                id="powerup_triple_exp",
                name="三倍经验卡",
                description="📚 使用后30分钟内经验翻三倍！",
                category=ItemCategory.POWER_UP,
                rarity=ItemRarity.EPIC,
                price=2000,
                emoji="📚",
                effect={"exp_multiplier": 3.0},
                duration_hours=1,
            ),
            ShopItem(
                id="powerup_hint_card",
                name="提示卡",
                description="💡 遇到难题时自动获得一条提示",
                category=ItemCategory.POWER_UP,
                rarity=ItemRarity.COMMON,
                price=200,
                emoji="💡",
                effect={"free_hint": True},
            ),
            ShopItem(
                id="powerup_skip_card",
                name="跳过卡",
                description="⏭️ 跳过当前题目，不减经验",
                category=ItemCategory.POWER_UP,
                rarity=ItemRarity.COMMON,
                price=300,
                emoji="⏭️",
                effect={"skip_no_penalty": True},
            ),
            ShopItem(
                id="powerup_time_freeze",
                name="时间冻结",
                description="⏰ 使用后研究时间不计入疲劳值，持续2小时",
                category=ItemCategory.POWER_UP,
                rarity=ItemRarity.RARE,
                price=1500,
                emoji="⏰",
                effect={"no_fatigue": True},
                duration_hours=2,
            ),

            # === 特权/服务 ===
            ShopItem(
                id="privilege_vip_week",
                name="VIP 周卡",
                description="🌟 7天内享受VIP特权：经验+50%，专属客服，优先体验新功能",
                category=ItemCategory.PRIVILEGE,
                rarity=ItemRarity.EPIC,
                price=5000,
                emoji="🌟",
                effect={"exp_bonus": 0.5, "priority": True},
                duration_hours=168,
            ),
            ShopItem(
                id="privilege_kg_access",
                name="知识图谱解锁",
                description="🕸️ 永久解锁知识图谱无限次查询（免费用户每天限5次）",
                category=ItemCategory.PRIVILEGE,
                rarity=ItemRarity.RARE,
                price=3000,
                emoji="🕸️",
                effect={"unlimited_kg": True},
            ),
        ]

        for item in default_items:
            self.items[item.id] = item

    def get_items(self, category: Optional[str] = None, rarity: Optional[str] = None) -> list[dict]:
        """获取商品列表（支持筛选）"""
        items = list(self.items.values())

        if category:
            items = [i for i in items if i.category.value == category]
        if rarity:
            items = [i for i in items if i.rarity.value == rarity]

        return [item.to_dict() for item in items]

    def get_item(self, item_id: str) -> Optional[ShopItem]:
        """获取单个商品"""
        return self.items.get(item_id)

    def purchase(self, user_id: str, item_id: str) -> dict:
        """
        购买商品

        Returns:
            {"success": bool, "message": str, "item": dict|None}
        """
        item = self.items.get(item_id)
        if not item:
            return {"success": False, "message": "商品不存在"}

        if item.stock == 0:
            return {"success": False, "message": "商品已售罄"}

        # 检查货币
        asset_service = get_user_asset_service()
        asset = asset_service.get_or_create_asset(user_id)

        if asset.total_copper_value < item.price:
            return {
                "success": False,
                "message": f"铜币不足！需要 {item.price}，当前 {asset.total_copper_value}",
                "needed": item.price - asset.total_copper_value,
            }

        # 扣除货币
        if not asset_service.spend_with_auto_exchange(user_id, item.price, f"购买 {item.name}"):
            return {"success": False, "message": "支付失败"}

        # 添加到背包
        if user_id not in asset_service._inventory:
            asset_service._inventory[user_id] = []
        asset_service._inventory[user_id].append(item_id)

        # 减少库存
        if item.stock > 0:
            item.stock -= 1

        # 如果是伙伴，自动装备
        if item.category == ItemCategory.COMPANION:
            asset_service.equip_companion(user_id, item_id)

        return {
            "success": True,
            "message": f"🎉 购买成功！{item.emoji} {item.name} 已加入背包",
            "item": item.to_dict(),
        }

    def format_price(self, price: int) -> str:
        """格式化价格显示"""
        gold = price // 10000
        silver = (price % 10000) // 100
        copper = price % 100

        parts = []
        if gold > 0:
            parts.append(f"🪙{gold}金")
        if silver > 0:
            parts.append(f"🥈{silver}银")
        if copper > 0:
            parts.append(f"🟤{copper}铜")

        return " ".join(parts) if parts else "免费"

    def get_shop_landing(self, user_id: str) -> dict:
        """获取商城首页数据"""
        asset_service = get_user_asset_service()
        asset = asset_service.get_or_create_asset(user_id)
        equipped = asset_service.get_equipped(user_id)
        inventory = asset_service.get_inventory(user_id)

        # 推荐商品（稀有度最高的非卖品）
        all_items = list(self.items.values())
        legendary = [i for i in all_items if i.rarity == ItemRarity.LEGENDARY]
        epic = [i for i in all_items if i.rarity == ItemRarity.EPIC]

        return {
            "user_asset": {
                "copper": asset.copper,
                "silver": asset.silver,
                "gold": asset.gold,
                "level": asset.level,
                "level_title": asset_service.get_level_title(asset.level),
            },
            "equipped_companion": equipped,
            "inventory": inventory,
            "recommended": [
                {"name": i.name, "emoji": i.emoji, "price": i.price, "rarity": i.rarity.value}
                for i in (legendary + epic)[:3]
            ],
            "total_items": len(self.items),
            "categories": {
                "companion": len([i for i in all_items if i.category == ItemCategory.COMPANION]),
                "cosmetic": len([i for i in all_items if i.category == ItemCategory.COSMETIC]),
                "power_up": len([i for i in all_items if i.category == ItemCategory.POWER_UP]),
                "privilege": len([i for i in all_items if i.category == ItemCategory.PRIVILEGE]),
            },
        }


def get_points_shop() -> PointsShop:
    """获取积分商城实例"""
    return PointsShop()
