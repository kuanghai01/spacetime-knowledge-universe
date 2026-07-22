"""
时空知识宇宙 - 腾讯云函数 SCF 入口
（HTTP REST API，无 WebSocket，适配云函数）
"""
import json
import logging
import traceback
from uuid import uuid4

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ===== 延迟初始化（云函数冷启动时执行一次） =====
_principal = None
_sessions = {}  # 内存中的学习会话（SCF 实例复用）


def _get_principal():
    """获取/初始化中枢校长 Agent"""
    global _principal
    if _principal is None:
        from src.core.router.principal_agent import get_principal_agent
        from src.agents.history_agent import get_history_agent
        from src.agents.physics_agent import get_physics_agent
        from src.agents.math_agent import get_math_agent

        _principal = get_principal_agent()
        _principal.register_agent("history", get_history_agent())
        _principal.register_agent("physics", get_physics_agent())
        _principal.register_agent("math", get_math_agent())
        logger.info("✅ 所有 Agent 已初始化")
    return _principal


def _get_learning_engine():
    """获取学习引擎"""
    from src.core.learning.engine import LearningEngine
    return LearningEngine()


# ===== 路由表 =====
ROUTES = {}


def route(method, path):
    """路由注册装饰器"""
    def decorator(func):
        key = (method.upper(), path)
        ROUTES[key] = func
        return func
    return decorator


# ===== API 实现 =====

@route("GET", "/api/health")
def health_check(event):
    return 200, {"status": "healthy", "version": "1.0.0", "mode": "scf"}


@route("GET", "/api/v1/learn/subjects")
def list_subjects(event):
    subjects = [
        {"id": "history", "name": "历史", "description": "穿越时空，亲历历史现场", "is_active": True},
        {"id": "physics", "name": "物理", "description": "探索万物运行的奥秘，虚拟实验室等你体验", "is_active": True},
        {"id": "math", "name": "数学", "description": "数形结合，探索数字的奥秘", "is_active": True},
    ]
    return 200, subjects


@route("GET", "/api/v1/learn/subjects/{subject_id}")
def get_subject(event, subject_id):
    subjects = {
        "history": {
            "id": "history", "name": "历史",
            "chapters": [
                {"id": "B7A", "title": "七年级上册", "kp_count": 16},
                {"id": "B7B", "title": "七年级下册", "kp_count": 18},
                {"id": "B8A", "title": "八年级上册", "kp_count": 12},
                {"id": "B8B", "title": "八年级下册", "kp_count": 10},
                {"id": "B9A", "title": "九年级上册", "kp_count": 41},
                {"id": "B9B", "title": "九年级下册", "kp_count": 15},
            ],
            "agent_name": "史博士", "total_knowledge_points": 112,
        },
        "physics": {
            "id": "physics", "name": "物理",
            "chapters": [
                {"id": "B8A", "title": "八年级上册", "kp_count": 23},
                {"id": "B8B", "title": "八年级下册", "kp_count": 19},
                {"id": "B9", "title": "九年级", "kp_count": 31},
            ],
            "agent_name": "物先生", "total_knowledge_points": 73,
        },
        "math": {
            "id": "math", "name": "数学",
            "chapters": [
                {"id": "B7A", "title": "七年级上册", "kp_count": 20},
                {"id": "B7B", "title": "七年级下册", "kp_count": 22},
                {"id": "B8A", "title": "八年级上册", "kp_count": 25},
                {"id": "B8B", "title": "八年级下册", "kp_count": 23},
                {"id": "B9A", "title": "九年级上册", "kp_count": 17},
                {"id": "B9B", "title": "九年级下册", "kp_count": 13},
            ],
            "agent_name": "数先生", "total_knowledge_points": 120,
        },
    }
    if subject_id not in subjects:
        return 404, {"error": "学科不存在"}
    return 200, subjects[subject_id]


@route("POST", "/api/v1/learn/start-session")
def start_session(event):
    """开始学习会话"""
    body = json.loads(event.get("body", "{}"))
    user_id = body.get("user_id", "anonymous")
    subject_id = body.get("subject_id", "history")
    mode = body.get("mode", "guided")

    engine = _get_learning_engine()
    session = engine.start_session(user_id, subject_id, mode)
    _sessions[session.session_id] = session

    subject_names = {"history": "历史", "physics": "物理", "math": "数学"}
    agent_names = {"history": "史博士", "physics": "物先生", "math": "数先生"}

    response = {
        "session_id": session.session_id,
        "mode": mode,
        "subject": subject_names.get(subject_id, subject_id),
        "agent": agent_names.get(subject_id, subject_id),
        "welcome": f"👋 欢迎来到{subject_names.get(subject_id, subject_id)}课堂！我是你的{agent_names.get(subject_id, subject_id)}。",
    }

    # 引导模式：自动出第一题
    if mode in ("guided", "hybrid"):
        question = engine.get_next_question(session.session_id)
        if question:
            response["question"] = _format_question(question)

    return 200, response


@route("POST", "/api/v1/learn/answer")
def submit_answer(event):
    """提交答案"""
    body = json.loads(event.get("body", "{}"))
    session_id = body.get("session_id", "")
    answer = body.get("answer", "").strip()

    if not session_id or session_id not in _sessions:
        return 400, {"error": "会话不存在或已过期"}

    engine = _get_learning_engine()
    result = engine.submit_answer(session_id, answer)

    if not result:
        return 400, {"error": "无法评估答案"}

    response = {
        "correct": result.correct,
        "score": result.score,
        "feedback": result.feedback,
        "explanation": result.explanation,
        "exp_gained": result.exp_gained,
        "knowledge_reinforced": result.knowledge_reinforced,
    }

    # 自动出下一题
    next_q = engine.get_next_question(session_id)
    if next_q:
        response["next_question"] = _format_question(next_q)
    else:
        response["finished"] = True
        response["message"] = "🎉 太棒了！所有知识点都练习完了！"

    return 200, response


@route("POST", "/api/v1/learn/free-question")
def free_question(event):
    """自由问答"""
    body = json.loads(event.get("body", "{}"))
    user_id = body.get("user_id", "anonymous")
    subject_id = body.get("subject_id", "history")
    message = body.get("message", "").strip()

    if not message:
        return 400, {"error": "问题不能为空"}

    # 使用演示模式响应
    from src.api.learn import get_demo_response
    demo = get_demo_response(subject_id, message)

    return 200, {
        "answer": demo["content"],
        "knowledge_points": demo.get("knowledge_points", []),
        "exp_gained": demo.get("exp_gained", 5),
    }


@route("POST", "/api/v1/learn/hint")
def get_hint(event):
    """获取提示"""
    body = json.loads(event.get("body", "{}"))
    session_id = body.get("session_id", "")

    if not session_id or session_id not in _sessions:
        return 400, {"error": "会话不存在"}

    engine = _get_learning_engine()
    hint = engine.get_hint(session_id)

    return 200, {"hint": hint}


@route("POST", "/api/v1/learn/end-session")
def end_session(event):
    """结束学习会话"""
    body = json.loads(event.get("body", "{}"))
    session_id = body.get("session_id", "")

    if not session_id or session_id not in _sessions:
        return 400, {"error": "会话不存在"}

    engine = _get_learning_engine()
    summary = engine.end_session(session_id)
    _sessions.pop(session_id, None)

    return 200, summary


@route("GET", "/api/v1/shop/items")
def shop_items(event):
    """获取商城商品"""
    from src.core.gamification.shop import PointsShop
    shop = PointsShop()
    items = shop.list_items()
    return 200, {"items": items}


@route("POST", "/api/v1/shop/buy")
def buy_item(event):
    """购买商品"""
    body = json.loads(event.get("body", "{}"))
    user_id = body.get("user_id", "anonymous")
    item_id = body.get("item_id", "")

    if not item_id:
        return 400, {"error": "商品ID不能为空"}

    # 简化版：直接返回成功
    return 200, {
        "success": True,
        "item_id": item_id,
        "message": "购买成功！（演示模式）",
    }


@route("GET", "/api/v1/assets")
def get_assets(event):
    """获取用户资产"""
    return 200, {
        "user_id": "anonymous",
        "level": 1,
        "exp": 0,
        "coins": {"copper": 100, "silver": 0, "gold": 0},
        "inventory": [],
    }


# ===== 辅助函数 =====

def _format_question(question):
    """格式化题目"""
    type_names = {"choice": "选择题", "fill_blank": "填空题", "short_answer": "简答题", "true_false": "判断题"}
    content = f"**{type_names.get(question.type.value, '题目')}**\n\n{question.content}"

    if question.options:
        letters = ["A", "B", "C", "D"]
        options_text = "\n".join(f"{letters[i]}. {opt}" for i, opt in enumerate(question.options))
        content += f"\n\n{options_text}"

    return {
        "question_id": question.id,
        "content": content,
        "question_type": question.type.value,
        "options": question.options,
        "difficulty": question.difficulty.value,
        "knowledge_point": question.knowledge_point_title,
    }


# ===== SCF 入口 =====

def main_handler(event, context):
    """
    腾讯云函数 SCF 入口函数
    
    event 格式（API Gateway 触发）：
    {
        "requestContext": {"serviceId": "...", "path": "/api/v1/...", "httpMethod": "GET"},
        "headers": {...},
        "body": "{\"key\": \"value\"}",
        "pathParameters": {"subject_id": "history"},
        "queryStringParameters": null,
        "httpMethod": "GET",
        "path": "/api/v1/learn/subjects/history",
        "queryString": null,
    }
    """
    try:
        # 解析请求
        http_method = event.get("httpMethod", "GET")
        path = event.get("path", "")
        headers = event.get("headers", {}) or {}
        path_params = event.get("pathParameters", {}) or {}
        query_params = event.get("queryStringParameters", {}) or {}

        logger.info(f"📨 {http_method} {path}")

        # 初始化（冷启动时执行）
        _get_principal()

        # 路由匹配
        handler = None
        path_params_found = {}

        # 精确匹配
        key = (http_method.upper(), path)
        if key in ROUTES:
            handler = ROUTES[key]
        else:
            # 路径参数匹配（如 /api/v1/learn/subjects/{subject_id}）
            for (m, p), h in ROUTES.items():
                if m != http_method.upper():
                    continue
                # 简单路径参数匹配
                if "{" in p:
                    p_parts = p.split("/")
                    path_parts = path.split("/")
                    if len(p_parts) == len(path_parts):
                        match = True
                        params = {}
                        for pp, ap in zip(p_parts, path_parts):
                            if pp.startswith("{") and pp.endswith("}"):
                                params[pp[1:-1]] = ap
                            elif pp != ap:
                                match = False
                                break
                        if match:
                            handler = h
                            path_params_found = params
                            break

        if not handler:
            return _make_response(404, {"error": f"未找到路由: {http_method} {path}"})

        # 执行处理函数
        result = handler(event, **path_params_found) if path_params_found else handler(event)

        if isinstance(result, tuple):
            status_code, body = result
        else:
            status_code, body = 200, result

        return _make_response(status_code, body)

    except Exception as e:
        logger.error(f"❌ 处理请求出错: {e}\n{traceback.format_exc()}")
        return _make_response(500, {"error": str(e)})


def _make_response(status_code, body):
    """构造 SCF 响应"""
    return {
        "isBase64Encoded": False,
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }
