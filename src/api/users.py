"""
API 路由 - 用户相关
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging

from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import settings
from src.models.user import UserCreate, UserResponse, UserDashboardResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["用户"])

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # 实际从数据库查询用户
    return {"id": user_id, "username": "test_user", "level": 1, "exp": 0}


@router.post("/register", response_model=dict)
async def register(user: UserCreate):
    """用户注册"""
    # 实际存入数据库
    return {
        "id": str(uuid4()),
        "username": user.username,
        "message": "注册成功"
    }


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
    # 实际验证数据库
    # 这里简化处理
    access_token = create_access_token(data={"sub": "test_user_id"})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@router.get("/me/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """获取用户仪表盘数据"""
    return {
        "user": {
            "id": current_user["id"],
            "username": current_user["username"],
            "level": current_user["level"],
            "exp": current_user["exp"],
            "next_level_exp": 100
        },
        "progress": [
            {"subject_id": "history", "subject_name": "历史", "mastery": 25, "chapter": "第三章"},
        ],
        "currency": {
            "knowledge_coin": 150,
            "energy": 80,
            "gem": 5
        },
        "achievements_count": 2,
        "streak_days": 3,
        "today_tasks": {
            "completed": 1,
            "total": 3
        }
    }


@router.get("/me/progress")
async def get_progress(current_user: dict = Depends(get_current_user)):
    """获取学习进度"""
    return {
        "subjects": [
            {
                "subject_id": "history",
                "subject_name": "历史",
                "total_mastery": 25,
                "chapters": [
                    {"id": "ch1", "title": "史前时期", "mastery": 100},
                    {"id": "ch2", "title": "夏商周", "mastery": 50},
                    {"id": "ch3", "title": "秦汉时期", "mastery": 0},
                ]
            }
        ]
    }


@router.get("/me/achievements")
async def get_achievements(current_user: dict = Depends(get_current_user)):
    """获取成就列表"""
    return {
        "unlocked": [
            {"id": "first_step", "name": "第一步", "unlocked_at": "2026-07-20T10:00:00"},
            {"id": "streak_3", "name": "三日坚持", "unlocked_at": "2026-07-22T10:00:00"},
        ],
        "locked": [
            {"id": "scholar_10", "name": "小学者", "progress": 5, "target": 10},
            {"id": "streak_7", "name": "一周达人", "progress": 3, "target": 7},
        ]
    }
