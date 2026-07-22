"""
时空知识宇宙 - 主入口

启动命令:
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from config.settings import settings
from src.api import api_router
from src.core.router.principal_agent import get_principal_agent
from src.core.parser.textbook_parser import get_textbook_parser
from src.agents.history_agent import get_history_agent
from src.agents.physics_agent import get_physics_agent
from src.agents.math_agent import get_math_agent
from src.core.knowledge_graph import get_neo4j_connection
from src.api.shop import router as shop_router
from src.api.knowledge_graph import router as kg_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("🚀 时空知识宇宙正在启动...")
    
    # 初始化中枢校长 Agent
    principal = get_principal_agent()
    
    # 注册学科 Agent
    history_agent = get_history_agent()
    principal.register_agent("history", history_agent)
    logger.info("✅ 历史 Agent 已注册")
    
    physics_agent = get_physics_agent()
    principal.register_agent("physics", physics_agent)
    logger.info("✅ 物理 Agent 已注册")
    
    math_agent = get_math_agent()
    principal.register_agent("math", math_agent)
    logger.info("✅ 数学 Agent 已注册")

    # 初始化知识图谱
    neo4j_conn = get_neo4j_connection()
    if neo4j_conn.is_available:
        neo4j_conn.initialize_schema()
        logger.info("✅ Neo4j 知识图谱已连接")
    else:
        logger.warning("⚠️ Neo4j 不可用，知识图谱功能已跳过")

    # 初始化教材解析模块
    textbook_parser = get_textbook_parser()
    logger.info("✅ 教材解析模块已初始化")
    
    # 未来注册更多 Agent
    # principal.register_agent("physics", get_physics_agent())
    # principal.register_agent("math", get_math_agent())
    
    logger.info("🌟 时空知识宇宙启动完成！")

    yield

    # 关闭时
    logger.info("👋 时空知识宇宙正在关闭...")
    neo4j_conn.close()


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="游戏化沉浸式AI学习系统",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(kg_router)
app.include_router(shop_router)

# 静态文件（前端页面）
public_dir = Path(__file__).resolve().parent.parent / "public"
if public_dir.exists():
    app.mount("/app", StaticFiles(directory=str(public_dir), html=True), name="public")


# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


# 根路由 - 重定向到前端页面
@app.get("/")
async def root():
    index_file = public_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "游戏化沉浸式AI学习系统",
        "docs": "/docs",
        "app": "/app",
        "api_prefix": settings.API_V1_PREFIX
    }


# 获取所有学科
@app.get(f"{settings.API_V1_PREFIX}/subjects")
async def list_all_subjects():
    """获取所有学科（包括未开放的）"""
    return {
        "available": [
            {"id": "history", "name": "历史", "status": "active", "agent": "史博士"},
            {"id": "physics", "name": "物理", "status": "active", "agent": "物先生"},
            {"id": "math", "name": "数学", "status": "active", "agent": "数先生"},
        ],
        "coming_soon": [
            {"id": "chemistry", "name": "化学", "status": "planned"},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
