"""API 路由包"""
from fastapi import APIRouter

from src.api.learn import router as learn_router
from src.api.users import router as users_router
from src.api.gamification import router as gamification_router
from src.api.textbooks import router as textbooks_router

api_router = APIRouter()

api_router.include_router(learn_router)
api_router.include_router(users_router)
api_router.include_router(gamification_router)
api_router.include_router(textbooks_router)

__all__ = ["api_router"]
