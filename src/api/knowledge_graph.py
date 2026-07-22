"""
知识图谱 API

提供 REST 接口:
- GET /api/v1/kg/health - 健康检查
- GET /api/v1/kg/stats - 图谱统计
- GET /api/v1/kg/search - 搜索节点
- GET /api/v1/kg/event/{name} - 事件因果分析
- GET /api/v1/kg/person/{name} - 人物网络分析
- GET /api/v1/kg/timeline/{dynasty} - 朝代时间线
- POST /api/v1/kg/seed - 填充种子数据
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from src.core.knowledge_graph import get_neo4j_connection
from src.core.knowledge_graph.service import get_kg_service
from src.core.knowledge_graph.seed_data import seed_history_kg

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/kg", tags=["知识图谱"])


@router.get("/health")
async def kg_health():
    """知识图谱健康检查"""
    conn = get_neo4j_connection()
    health = conn.health_check()
    return {"status": "ok", **health}


@router.get("/stats")
async def kg_stats():
    """获取知识图谱统计"""
    conn = get_neo4j_connection()
    if not conn.is_available:
        raise HTTPException(status_code=503, detail="Neo4j 不可用")

    service = get_kg_service()
    return service.get_graph_statistics()


@router.get("/search")
async def kg_search(keyword: str, limit: int = 10):
    """搜索知识图谱节点"""
    conn = get_neo4j_connection()
    if not conn.is_available:
        raise HTTPException(status_code=503, detail="Neo4j 不可用")

    repo = conn  # type: ignore
    from src.core.knowledge_graph.repository import get_kg_repository
    repo = get_kg_repository()
    results = repo.search_nodes(keyword, limit=limit)

    return {"keyword": keyword, "results": results, "total": len(results)}


@router.get("/event/{event_name}")
async def kg_analyze_event(event_name: str):
    """分析历史事件（因果链）"""
    conn = get_neo4j_connection()
    if not conn.is_available:
        raise HTTPException(status_code=503, detail="Neo4j 不可用")

    service = get_kg_service()
    analysis = service.analyze_event(event_name)

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"未找到事件「{event_name}」"
        )

    return analysis


@router.get("/person/{person_name}")
async def kg_analyze_person(person_name: str):
    """分析历史人物"""
    conn = get_neo4j_connection()
    if not conn.is_available:
        raise HTTPException(status_code=503, detail="Neo4j 不可用")

    service = get_kg_service()
    analysis = service.analyze_person(person_name)

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"未找到人物「{person_name}」"
        )

    return analysis


@router.get("/timeline/{dynasty_name}")
async def kg_timeline(dynasty_name: str):
    """获取朝代时间线"""
    conn = get_neo4j_connection()
    if not conn.is_available:
        raise HTTPException(status_code=503, detail="Neo4j 不可用")

    service = get_kg_service()
    timeline = service.get_timeline(dynasty_name)

    if not timeline:
        raise HTTPException(
            status_code=404,
            detail=f"未找到朝代「{dynasty_name}」"
        )

    return timeline


@router.get("/causal/{event_name}")
async def kg_causal_explanation(event_name: str):
    """获取事件因果解释（自然语言）"""
    conn = get_neo4j_connection()
    if not conn.is_available:
        raise HTTPException(status_code=503, detail="Neo4j 不可用")

    service = get_kg_service()
    explanation = service.get_causal_explanation(event_name)

    if not explanation:
        raise HTTPException(
            status_code=404,
            detail=f"未找到事件「{event_name}」"
        )

    return {"event_name": event_name, "explanation": explanation}


@router.post("/seed")
async def kg_seed():
    """填充历史知识图谱种子数据"""
    conn = get_neo4j_connection()
    if not conn.is_available:
        raise HTTPException(status_code=503, detail="Neo4j 不可用")

    try:
        seed_history_kg()
        service = get_kg_service()
        stats = service.get_graph_statistics()
        return {"status": "success", "message": "历史知识图谱种子数据填充完成", "statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"填充失败: {str(e)}")
