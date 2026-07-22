"""
用户资产和积分商城 API

资产端点:
- GET  /api/v1/shop/                商城首页
- GET  /api/v1/shop/items           商品列表
- GET  /api/v1/shop/items/{id}      商品详情
- POST /api/v1/shop/buy/{item_id}  购买商品
- GET  /api/v1/shop/inventory       我的背包
- POST /api/v1/shop/equip/{item_id} 装备宠物

用户资产端点:
- GET  /api/v1/assets/              我的资产
- GET  /api/v1/assets/transactions  资产变动历史
- GET  /api/v1/assets/level         等级信息
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.core.gamification.user_asset import get_user_asset_service, CurrencyType
from src.core.gamification.shop import get_points_shop, ItemCategory

logger = logging.getLogger(__name__)

router = APIRouter()
asset_service = get_user_asset_service()
shop = get_points_shop()


# ============================
# 商城端点
# ============================

@router.get("/api/v1/shop/")
async def shop_landing():
    """商城首页"""
    return shop.get_shop_landing("anonymous")


@router.get("/api/v1/shop/items")
async def shop_items(
    category: Optional[str] = Query(None, description="分类筛选"),
    rarity: Optional[str] = Query(None, description="稀有度筛选"),
):
    """商品列表"""
    items = shop.get_items(category=category, rarity=rarity)
    return {"items": items, "total": len(items)}


@router.get("/api/v1/shop/items/{item_id}")
async def shop_item_detail(item_id: str):
    """商品详情"""
    item = shop.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")

    result = item.to_dict()
    result["price_formatted"] = shop.format_price(item.price)
    return result


@router.post("/api/v1/shop/buy/{item_id}")
async def shop_buy(item_id: str, user_id: str = Query("anonymous")):
    """购买商品"""
    result = shop.purchase(user_id, item_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/api/v1/shop/inventory")
async def shop_inventory(user_id: str = Query("anonymous")):
    """我的背包"""
    inventory = asset_service.get_inventory(user_id)
    items = []
    for item_id in inventory:
        item = shop.get_item(item_id)
        if item:
            items.append(item.to_dict())

    return {"inventory": items, "total": len(items)}


@router.post("/api/v1/shop/equip/{item_id}")
async def shop_equip(item_id: str, user_id: str = Query("anonymous")):
    """装备宠物"""
    success = asset_service.equip_companion(user_id, item_id)
    if not success:
        raise HTTPException(status_code=400, detail="无法装备：物品不在背包中")

    return {"success": True, "message": f"已装备 {item_id}"}


# ============================
# 用户资产端点
# ============================

@router.get("/api/v1/assets/")
async def get_assets(user_id: str = Query("anonymous")):
    """获取用户资产"""
    asset = asset_service.get_or_create_asset(user_id)
    return {
        "user_id": asset.user_id,
        "copper": asset.copper,
        "silver": asset.silver,
        "gold": asset.gold,
        "total_value": asset.total_copper_value,
        "exp": asset.exp,
        "level": asset.level,
        "level_title": asset_service.get_level_title(asset.level),
    }


@router.get("/api/v1/assets/transactions")
async def get_transactions(
    user_id: str = Query("anonymous"),
    limit: int = Query(20, ge=1, le=100),
):
    """获取资产变动历史"""
    txs = asset_service.get_transactions(user_id, limit=limit)
    return {
        "transactions": [
            {
                "currency": tx.currency.value,
                "amount": tx.amount,
                "reason": tx.reason,
                "timestamp": tx.timestamp.isoformat(),
                "balance_after": tx.balance_after,
            }
            for tx in txs
        ],
        "total": len(txs),
    }


@router.get("/api/v1/assets/level")
async def get_level_info(user_id: str = Query("anonymous")):
    """获取等级详情"""
    asset = asset_service.get_or_create_asset(user_id)
    current_level_base = (asset.level - 1) * (asset.level - 1) * 100 if asset.level > 1 else 0
    next_level_exp = asset.next_level_exp

    return {
        "level": asset.level,
        "title": asset_service.get_level_title(asset.level),
        "current_exp": asset.exp,
        "next_level_exp": next_level_exp,
        "progress": asset.current_level_progress,
        "exp_to_next": max(0, next_level_exp - asset.exp),
        "percent": round(asset.current_level_progress * 100, 1),
    }


@router.post("/api/v1/assets/add_exp")
async def add_experience(amount: int = Query(..., gt=0), user_id: str = Query("anonymous")):
    """增加经验（测试用）"""
    result = asset_service.add_experience(user_id, amount, "测试增加")
    return result


@router.post("/api/v1/assets/add_coins")
async def add_coins(amount: int = Query(..., gt=0), user_id: str = Query("anonymous")):
    """增加铜币（测试用）"""
    asset = asset_service.add_currency(user_id, CurrencyType.COPPER, amount, "测试增加")
    return {"success": True, "copper": asset.copper, "total": asset.total_copper_value}
