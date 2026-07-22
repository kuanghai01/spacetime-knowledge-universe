"""
API 路由 - 教材解析与知识图谱
"""
import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from src.api.users import get_current_user
from src.core.parser.textbook_parser import get_textbook_parser, TextbookParser, ParseResult
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/textbooks", tags=["教材解析"])


# 临时存储解析状态（实际应放入 Redis/DB）
_parse_statuses: dict[str, dict] = {}


@router.post("/upload")
async def upload_textbook(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    subject_id: str = "history",
    publisher: str = "人教版",
    grade: str = "七年级",
    current_user: dict = Depends(get_current_user),
):
    """
    上传教材 PDF 进行解析
    
    支持 PDF/JPG/PNG，解析完成后自动提取知识点并生成知识图谱
    """
    # 检查文件类型
    allowed_types = [".pdf", ".jpg", ".jpeg", ".png"]
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}，请上传 PDF 或图片"
        )
    
    # 检查 OpenAI API Key
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="系统未配置 OPENAI_API_KEY，无法进行教材解析"
        )
    
    # 保存临时文件
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename or "upload.pdf")
    
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    task_id = str(uuid4())
    
    # 后台任务解析
    _parse_statuses[task_id] = {
        "id": task_id,
        "status": "parsing",
        "progress": 0,
        "message": "正在解析教材...",
        "subject_id": subject_id,
        "filename": file.filename,
    }
    
    background_tasks.add_task(
        _parse_textbook_task,
        task_id=task_id,
        file_path=temp_path,
        subject_id=subject_id,
        publisher=publisher,
        grade=grade,
    )
    
    return {
        "task_id": task_id,
        "status": "parsing",
        "message": "教材上传成功，正在后台解析，请通过 /{task_id}/status 查询进度"
    }


@router.get("/{task_id}/status")
async def get_parse_status(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """查询教材解析状态"""
    if task_id not in _parse_statuses:
        raise HTTPException(status_code=404, detail="解析任务不存在")
    
    return _parse_statuses[task_id]


@router.get("/{task_id}/knowledge-map")
async def get_knowledge_map(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取解析后的知识图谱"""
    status = _parse_statuses.get(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="解析任务不存在")
    
    if status.get("status") != "completed":
        raise HTTPException(status_code=202, detail="解析尚未完成")
    
    result = status.get("result", {})
    return {
        "task_id": task_id,
        "knowledge_points": result.get("knowledge_points", []),
        "knowledge_graph": result.get("knowledge_graph", {}),
        "total_knowledge_points": len(result.get("knowledge_points", [])),
    }


@router.get("/{task_id}/knowledge-points")
async def get_knowledge_points(
    task_id: str,
    chapter: Optional[str] = None,
    difficulty: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
):
    """获取解析出的知识点列表（支持筛选）"""
    status = _parse_statuses.get(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="解析任务不存在")
    
    if status.get("status") != "completed":
        raise HTTPException(status_code=202, detail="解析尚未完成")
    
    result = status.get("result", {})
    kps = result.get("knowledge_points", [])
    
    # 筛选
    if chapter:
        kps = [kp for kp in kps if kp.get("chapter") == chapter]
    if difficulty:
        kps = [kp for kp in kps if kp.get("difficulty") == difficulty]
    
    return {
        "task_id": task_id,
        "knowledge_points": kps,
        "total": len(kps),
    }


@router.get("/{task_id}/chapters")
async def get_chapters(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取教材章节列表"""
    status = _parse_statuses.get(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="解析任务不存在")
    
    if status.get("status") != "completed":
        raise HTTPException(status_code=202, detail="解析尚未完成")
    
    result = status.get("result", {})
    structure = result.get("structure", {})
    sections = structure.get("sections", [])
    
    return {
        "task_id": task_id,
        "chapters": [
            {"title": s.title, "level": s.level}
            for s in sections
        ]
    }


async def _parse_textbook_task(
    task_id: str,
    file_path: str,
    subject_id: str,
    publisher: str,
    grade: str,
):
    """后台解析任务"""
    try:
        parser = get_textbook_parser()
        
        # 更新进度
        _parse_statuses[task_id]["progress"] = 10
        
        # 执行解析
        result = await parser.parse(
            file_path=file_path,
            subject_id=subject_id,
            publisher=publisher,
            grade=grade,
        )
        
        if result.success:
            _parse_statuses[task_id].update({
                "status": "completed",
                "progress": 100,
                "message": "解析完成",
                "result": {
                    "knowledge_points": [
                        {
                            "id": kp.id,
                            "title": kp.title,
                            "content": kp.content,
                            "chapter": kp.chapter,
                            "difficulty": kp.difficulty,
                            "tags": kp.tags,
                        }
                        for kp in result.knowledge_points
                    ],
                    "knowledge_graph": result.knowledge_graph,
                    "structure": {
                        "sections": [
                            {"title": s.title, "level": s.level}
                            for s in (result.structure.sections if result.structure else [])
                        ]
                    }
                }
            })
        else:
            _parse_statuses[task_id].update({
                "status": "error",
                "message": result.error_message or "解析失败",
            })
    
    except Exception as e:
        logger.error(f"教材解析任务 {task_id} 失败: {e}")
        _parse_statuses[task_id].update({
            "status": "error",
            "message": str(e),
        })
    
    finally:
        # 清理临时文件
        try:
            os.remove(file_path)
        except Exception:
            pass
