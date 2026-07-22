"""
时空知识宇宙 - Render 精简版主入口
（无 PostgreSQL/Redis/Neo4j/Milvus 依赖，纯内存运行）
"""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from config.settings import settings
from src.core.router.principal_agent import get_principal_agent
from src.agents.history_agent import get_history_agent
from src.agents.physics_agent import get_physics_agent
from src.agents.math_agent import get_math_agent
from src.api.learn import router as learn_router
from src.api.shop import router as shop_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 前端静态文件目录
public_dir = Path(__file__).resolve().parent.parent / "public"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 时空知识宇宙正在启动...")

    # 初始化中枢校长 Agent
    principal = get_principal_agent()

    # 注册学科 Agent
    principal.register_agent("history", get_history_agent())
    logger.info("✅ 历史 Agent 已注册")

    principal.register_agent("physics", get_physics_agent())
    logger.info("✅ 物理 Agent 已注册")

    principal.register_agent("math", get_math_agent())
    logger.info("✅ 数学 Agent 已注册")

    logger.info("🌟 时空知识宇宙启动完成！")
    yield
    logger.info("👋 时空知识宇宙正在关闭...")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="游戏化沉浸式 AI 学习系统",
    lifespan=lifespan,
)

# CORS 配置（允许 GitHub Pages 访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
# learn_router 已内置 /learn 前缀，只需加 /api/v1
app.include_router(learn_router, prefix=settings.API_V1_PREFIX)
# shop_router 已内置完整路径 /api/v1/shop/，不加前缀
app.include_router(shop_router)

# 静态文件（前端）
if public_dir.exists():
    app.mount("/static", StaticFiles(directory=str(public_dir)), name="public")


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    """根路径 - 返回前端页面"""
    if (public_dir / "index.html").exists():
        from fastapi.responses import FileResponse
        return FileResponse(str(public_dir / "index.html"))
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
    }
