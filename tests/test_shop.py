"""
测试 - 用户资产和商城
"""
import pytest
from unittest.mock import MagicMock, patch

from src.core.gamification.user_asset import (
    UserAssetService, UserAsset, AssetTransaction, CurrencyType, get_user_asset_service,
)
from src.core.gamification.shop import (
    PointsShop, ShopItem, ItemCategory, ItemRarity, get_points_shop,
)


class TestUserAssetService:
    """用户资产服务测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每次测试前重置"""
        service = get_user_asset_service()
        service.reset()
        yield
        service.reset()

    @pytest.fixture
    def service(self):
        return get_user_asset_service()

    def test_create_asset(self, service):
        """测试创建用户资产"""
        asset = service.get_or_create_asset("user1")
        assert asset.user_id == "user1"
        assert asset.copper == 0
        assert asset.level == 1

    def test_add_copper(self, service):
        """测试增加铜币"""
        service.add_currency("user1", CurrencyType.COPPER, 50, "测试")
        asset = service.get_asset("user1")
        assert asset.copper == 50

    def test_auto_exchange_copper_to_silver(self, service):
        """测试铜币自动兑换银币"""
        service.add_currency("user1", CurrencyType.COPPER, 250, "测试")
        asset = service.get_asset("user1")
        assert asset.silver == 2
        assert asset.copper == 50

    def test_auto_exchange_silver_to_gold(self, service):
        """测试银币自动兑换金币"""
        service.add_currency("user1", CurrencyType.SILVER, 150, "测试")
        asset = service.get_asset("user1")
        assert asset.gold == 1
        assert asset.silver == 50

    def test_spend_currency_success(self, service):
        """测试成功消费"""
        service.add_currency("user1", CurrencyType.COPPER, 150)
        # 150 copper → 1 silver + 50 copper (auto-exchange)
        result = service.spend_currency("user1", CurrencyType.COPPER, 30, "消费")
        assert result is True
        assert service.get_asset("user1").copper == 20
        assert service.get_asset("user1").silver == 1

    def test_spend_currency_insufficient(self, service):
        """测试余额不足"""
        service.add_currency("user1", CurrencyType.COPPER, 30)
        result = service.spend_currency("user1", CurrencyType.COPPER, 50)
        assert result is False

    def test_smart_payment_with_exchange(self, service):
        """测试智能支付（自动兑换）"""
        # 给1金币=10000铜币
        service.add_currency("user1", CurrencyType.GOLD, 1)
        # 消费500铜币
        result = service.spend_with_auto_exchange("user1", 500, "测试支付")
        assert result is True

    def test_smart_payment_insufficient(self, service):
        """测试智能支付余额不足"""
        service.add_currency("user1", CurrencyType.COPPER, 10)
        result = service.spend_with_auto_exchange("user1", 5000)
        assert result is False

    def test_add_experience_no_level_up(self, service):
        """测试增加经验（不升级）"""
        result = service.add_experience("user1", 50)
        assert result["level_up"] is False
        assert result["new_level"] == 1
        assert result["exp_gained"] == 50

    def test_add_experience_with_level_up(self, service):
        """测试增加经验并升级"""
        result = service.add_experience("user1", 500)
        assert result["level_up"] is True
        assert result["new_level"] > 1

    def test_level_progress(self, service):
        """测试等级进度计算"""
        asset = service.get_or_create_asset("user1")
        asset.exp = 50
        assert 0 < asset.current_level_progress < 1

    def test_next_level_exp(self, service):
        """测试下一级经验"""
        asset = service.get_or_create_asset("user1")
        assert asset.next_level_exp == 100  # Lv.1 → Lv.2 = 4*100? 等等

    def test_get_level_title(self, service):
        """测试等级称号"""
        assert service.get_level_title(1) == "初学者"
        assert service.get_level_title(10) == "中学生"
        assert service.get_level_title(50) == "大师"

    def test_purchase_item(self, service):
        """测试购买物品"""
        service.add_currency("user1", CurrencyType.COPPER, 1000)
        result = service.purchase_item("user1", "test_item", 500)
        assert result is True
        assert "test_item" in service.get_inventory("user1")

    def test_purchase_item_insufficient_funds(self, service):
        """测试购买物品余额不足"""
        service.add_currency("user1", CurrencyType.COPPER, 100)
        result = service.purchase_item("user1", "expensive", 5000)
        assert result is False

    def test_equip_companion(self, service):
        """测试装备宠物"""
        service.add_currency("user1", CurrencyType.COPPER, 5000)
        service.purchase_item("user1", "companion_cat", 2000)
        result = service.equip_companion("user1", "companion_cat")
        assert result is True
        assert service.get_equipped("user1") == "companion_cat"

    def test_equip_companion_not_owned(self, service):
        """测试装备未拥有的宠物"""
        result = service.equip_companion("user1", "not_owned")
        assert result is False

    def test_transaction_history(self, service):
        """测试交易记录"""
        service.add_currency("user1", CurrencyType.COPPER, 150, "收入")
        service.spend_currency("user1", CurrencyType.COPPER, 30, "支出")
        txs = service.get_transactions("user1")
        assert len(txs) >= 2


class TestPointsShop:
    """积分商城测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每次测试前重置"""
        service = get_user_asset_service()
        service.reset()
        yield
        service.reset()

    @pytest.fixture
    def shop(self):
        return get_points_shop()

    def test_init_default_items(self, shop):
        """测试初始化默认商品"""
        assert len(shop.items) > 0

    def test_get_items_all(self, shop):
        """测试获取所有商品"""
        items = shop.get_items()
        assert len(items) >= 10

    def test_get_items_by_category(self, shop):
        """测试按分类筛选"""
        companions = shop.get_items(category="companion")
        assert len(companions) >= 3
        assert all(i["category"] == "companion" for i in companions)

    def test_get_items_by_rarity(self, shop):
        """测试按稀有度筛选"""
        legendaries = shop.get_items(rarity="legendary")
        assert len(legendaries) >= 1
        assert all(i["rarity"] == "legendary" for i in legendaries)

    def test_get_item(self, shop):
        """测试获取单个商品"""
        item = shop.get_item("companion_cat")
        assert item is not None
        assert item.name == "知识小猫"

    def test_get_item_not_found(self, shop):
        """测试商品不存在"""
        item = shop.get_item("nonexistent")
        assert item is None

    def test_purchase_success(self, shop):
        """测试成功购买"""
        # 给用户足够的钱
        service = get_user_asset_service()
        service.get_or_create_asset("buyer")
        service.add_currency("buyer", CurrencyType.COPPER, 5000)
        result = shop.purchase("buyer", "companion_panda")
        assert result["success"] is True
        assert "companion_panda" in service.get_inventory("buyer")

    def test_purchase_insufficient_funds(self, shop):
        """测试余额不足购买失败"""
        service = get_user_asset_service()
        service.get_or_create_asset("poor_user")
        service.add_currency("poor_user", CurrencyType.COPPER, 10)
        result = shop.purchase("poor_user", "companion_dragon")
        assert result["success"] is False

    def test_purchase_not_exist(self, shop):
        """测试购买不存在的商品"""
        result = shop.purchase("user", "nonexistent")
        assert result["success"] is False

    def test_format_price(self, shop):
        """测试价格格式化"""
        assert "铜" in shop.format_price(50)
        assert "银" in shop.format_price(500)
        assert "金" in shop.format_price(50000)

    def test_shop_landing(self, shop):
        """测试商城首页数据"""
        landing = shop.get_shop_landing("anonymous")
        assert "user_asset" in landing
        assert "recommended" in landing
        assert "categories" in landing

    def test_item_to_dict(self, shop):
        """测试商品序列化"""
        item = shop.get_item("companion_cat")
        d = item.to_dict()
        assert "id" in d
        assert "name" in d
        assert "rarity_color" in d
