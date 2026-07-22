"""
API 路由 - 学习相关
"""
import json
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional
from uuid import UUID
import logging

from src.models.schemas import (
    SubjectResponse,
    ChapterResponse,
    KnowledgePointResponse,
    TextbookUploadRequest,
    TextbookResponse,
    StudyRecordCreate,
)
from src.core.router.principal_agent import get_principal_agent
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learn", tags=["学习"])


@router.get("/subjects", response_model=list[SubjectResponse])
async def list_subjects():
    """获取所有可用学科"""
    return [
        SubjectResponse(
            id="history",
            name="历史",
            description="穿越时空，亲历历史现场",
            icon_url="/icons/history.png",
            is_active=True
        ),
        SubjectResponse(
            id="physics",
            name="物理",
            description="探索万物运行的奥秘，虚拟实验室等你体验",
            icon_url="/icons/physics.png",
            is_active=True
        ),
        SubjectResponse(
            id="math",
            name="数学",
            description="数形结合，探索数字的奥秘",
            icon_url="/icons/math.png",
            is_active=True
        ),
    ]


@router.get("/subjects/{subject_id}")
async def get_subject_detail(subject_id: str):
    """获取学科详情"""
    if subject_id == "history":
        return {
            "id": "history",
            "name": "历史",
            "description": "穿越时空，亲历历史现场",
            "chapters": [
                {"id": "ch1", "title": "第一章 史前时期", "mastery": 0},
                {"id": "ch2", "title": "第二章 夏商周", "mastery": 0},
                {"id": "ch3", "title": "第三章 秦汉时期", "mastery": 0},
                {"id": "ch4", "title": "第四章 西汉与东汉", "mastery": 0},
            ],
            "total_knowledge_points": 50,
            "agent_name": "史博士"
        }
    elif subject_id == "physics":
        return {
            "id": "physics",
            "name": "物理",
            "description": "探索万物运行的奥秘",
            "chapters": [
                {"id": "ch1", "title": "第一章 力学", "mastery": 0},
                {"id": "ch2", "title": "第二章 光学", "mastery": 0},
                {"id": "ch3", "title": "第三章 电学", "mastery": 0},
            ],
            "total_knowledge_points": 40,
            "agent_name": "物先生",
            "virtual_experiments": 4,
        }
    elif subject_id == "math":
        return {
            "id": "math",
            "name": "数学",
            "description": "数形结合，探索数字的奥秘",
            "chapters": [
                {"id": "ch1", "title": "第一章 数与式", "mastery": 0},
                {"id": "ch2", "title": "第二章 方程与不等式", "mastery": 0},
                {"id": "ch3", "title": "第三章 函数", "mastery": 0},
                {"id": "ch4", "title": "第四章 图形与几何", "mastery": 0},
            ],
            "total_knowledge_points": 50,
            "agent_name": "数先生",
            "visualizations": 4,
        }
    raise HTTPException(status_code=404, detail="学科不存在")


@router.get("/subjects/{subject_id}/chapters/{chapter_id}")
async def get_chapter_detail(subject_id: str, chapter_id: str):
    """获取章节详情"""
    if subject_id == "history":
        return {
            "chapter_id": chapter_id,
            "subject_id": subject_id,
            "title": "第三章 秦汉时期",
            "sections": [
                {"id": "sec1", "title": "秦始皇统一六国", "knowledge_points": 5},
                {"id": "sec2", "title": "秦朝的统治措施", "knowledge_points": 4},
                {"id": "sec3", "title": "秦末农民起义", "knowledge_points": 3},
            ],
            "mastery_level": 0,
            "estimated_time_minutes": 45
        }
    elif subject_id == "physics":
        return {
            "chapter_id": chapter_id,
            "subject_id": subject_id,
            "title": "第二章 光学",
            "sections": [
                {"id": "sec1", "title": "光的直线传播", "knowledge_points": 3},
                {"id": "sec2", "title": "光的反射", "knowledge_points": 4},
                {"id": "sec3", "title": "光的折射", "knowledge_points": 3},
            ],
            "mastery_level": 0,
            "estimated_time_minutes": 40,
            "has_virtual_experiments": True,
        }
    return {"chapter_id": chapter_id, "title": "章节", "sections": []}


@router.get("/knowledge/{kp_id}")
async def get_knowledge_point(kp_id: str):
    """获取知识点详情"""
    return {
        "id": kp_id,
        "title": "知识点详情",
        "content": "这里是知识点的详细内容...",
        "difficulty": 2,
        "tags": ["示例"],
        "related_knowledge": [],
        "prerequisites": [],
    }


# 演示模式回应（当没有 API key 时使用）
def get_demo_response(subject: str, message: str) -> dict:
    """生成演示模式响应"""
    if subject == "history":
        if "秦始皇" in message or "统一" in message:
            return {
                "content": "**让我们穿越回公元前221年...**\n\n秦王嬴政先后灭韩、赵、魏、楚、燕、齐六国，完成了中国历史上第一次大一统！\n\n**你知道吗？** 秦始皇统一后做了这三件大事：\n1. 统一文字（小篆）\n2. 统一货币（圆形方孔钱）\n3. 统一度量衡\n\n💡 **思考题**：如果你是嬴政，你会先攻打哪个国家？",
                "knowledge_points": ["秦始皇统一六国", "秦朝巩固措施"],
                "exp_gained": 15,
            }
        elif "起义" in message or "陈胜" in message:
            return {
                "content": "**大泽乡的一场雨，改变了中国历史...**\n\n公元前209年，陈胜、吴广等900多名农民被征发去渔阳守边。途中遇到大雨，无法按期到达。按秦律，误期当斩。\n\n陈胜喊出了那句千古名言：**\"王侯将相，宁有种乎！\"**\n\n这是中国历史上第一次大规模农民起义！",
                "knowledge_points": ["陈胜吴广起义", "秦朝灭亡"],
                "exp_gained": 12,
            }
        else:
            return {
                "content": f"欢迎来到历史时空！\n\n你刚问到的是关于\"{message}\"的问题。历史是一门有趣的学科，它告诉我们过去发生了什么，以及为什么。\n\n你可以问我关于中国古代史的任何问题，比如：\n- 秦始皇统一六国的过程\n- 丝绸之路的故事\n- 四大发明的诞生\n- 各个朝代的兴衰\n\n告诉我你想了解哪段历史？📚",
                "knowledge_points": [],
                "exp_gained": 5,
            }
    
    elif subject == "physics":
        if "光" in message and ("实验" in message or "演示" in message):
            return {
                "content": "🧪 **虚拟实验室：观察影子的形成**\n\n**实验目的**\n观察光的直线传播现象\n\n**实验步骤**\n1. 准备手电筒和白屏\n2. 将卡纸放在手电筒和白屏之间\n3. 打开手电筒，观察白屏上的影子\n4. 改变卡纸与手电筒的距离，观察影子变化\n\n**观察与记录**\n• 光沿直线传播，遇到不透明物体时被阻挡\n• 影子大小与物体到光源的距离有关\n• 影子轮廓与物体形状相似\n\n💡 **小挑战**：你能用家里的物品设计一个类似的小实验吗？\n\n---\n*来自时空知识宇宙·虚拟实验室* 🔬",
                "knowledge_points": ["光的直线传播"],
                "virtual_experiment": "exp_light_001",
                "exp_gained": 20,
            }
        elif "光" in message and ("传播" in message or "反射" in message or "折射" in message):
            return {
                "content": "**光的奥秘** 🔦\n\n光在同一种均匀介质中沿直线传播。当光遇到不同介质界面时，会发生反射或折射。\n\n**三个重要概念**：\n1. **光的直线传播**：光在同一种均匀介质中沿直线传播\n2. **光的反射**：反射角等于入射角\n3. **光的折射**：光从空气斜射入水中时，折射角小于入射角\n\n**生活中的应用**：\n- 镜子成像 = 光的反射\n- 筷子在水里\"弯折\" = 光的折射\n- 日食月食 = 光的直线传播\n\n想通过虚拟实验亲眼看看这些现象吗？试试说\"帮我做个光的实验\"！",
                "knowledge_points": ["光的直线传播", "光的反射定律", "光的折射"],
                "exp_gained": 18,
            }
        elif "牛顿" in message or "惯性" in message:
            return {
                "content": "**牛顿第一定律（惯性定律）** 🎾\n\n一切物体在不受外力作用时，总保持静止状态或匀速直线运动状态。\n\n**什么是惯性？**\n物体保持运动状态不变的性质叫做惯性。质量越大，惯性越大。\n\n**生活中的惯性**：\n- 汽车刹车时，你会向前倾（身体保持运动状态）\n- 用力甩手，手上的水被甩出去\n- 跳远时助跑，利用惯性跳更远\n\n💡 **想一想**：太空中的宇航员为什么可以漂浮？（提示：没有空气阻力！）",
                "knowledge_points": ["牛顿第一定律", "惯性"],
                "exp_gained": 15,
            }
        else:
            return {
                "content": f"欢迎来到物理世界！⚗️\n\n你刚问的是关于\"{message}\"的问题。\n\n**我能带你探索**：\n- ⚡ 电学（电路、电压、电阻）\n- 🔦 光学（反射、折射、透镜）\n- ⚙️ 力学（运动、力、能量）\n- 🔊 声学（振动、波）\n\n**特别推荐**：试试说\"帮我做个XX实验\"，物理虚拟实验室等你来探索！\n\n你想了解哪个物理现象？",
                "knowledge_points": [],
                "exp_gained": 5,
            }
    
    elif subject == "math":
        if "方程" in message or "求解" in message or "解" in message:
            return {
                "content": "📝 **解方程步步为营**\n\n解方程的核心思想：让未知数单独站在等号的一边。\n\n**解题四步法**：\n1. **审题**：找出已知和未知\n2. **移项**：把含未知数的项移到一边，常数项另一边（切记：移项要变号！）\n3. **合并**：简化等式两边\n4. **求解**：系数化为1\n\n**易错点提醒** ⚠️：\n- 移项时必须变号（+ 变 -，- 变 +）\n- 去括号时，括号前是负号，括号内每一项都要变号\n- 系数为负数时，不等号方向要改变\n\n💡 **小练习**：解方程 2x + 5 = 13，你能在心里算出 x = ?",
                "knowledge_points": ["一元一次方程", "等式性质"],
                "exp_gained": 18,
            }
        elif "函数" in message or "图像" in message or "直线" in message:
            return {
                "content": "📈 **一次函数 y = kx + b**\n\n一次函数的图像是一条直线，由两个参数决定：\n\n**k（斜率）** —— 决定直线的倾斜程度\n- k > 0：直线上升（越往右越高）\n- k < 0：直线下降（越往右越低）\n- |k| 越大：直线越陡峭\n\n**b（截距）** —— 决定直线与 y 轴交点\n- b > 0：直线交 y 轴正半轴\n- b < 0：直线交 y 轴负半轴\n\n**经典例子**：\n- y = 2x + 1（向上倾斜，过点(0,1)）\n- y = -x + 3（向下倾斜，过点(0,3)）\n\n💡 **想一想**：k=0 时图像是什么样子？",
                "knowledge_points": ["一次函数的图像与性质", "斜率与截距"],
                "exp_gained": 18,
            }
        elif "三角形" in message or "角度" in message or "内角" in message:
            return {
                "content": "🔺 **三角形内角和定理**\n\n三角形的三个内角的和等于 **180°**。\n\n**验证方法**：\n1. 📐 **度量法**：量出三个角的度数，相加\n2. ✂️ **折纸法**：剪下三个角，拼成平角\n3. 📏 **推理法**：作平行线，利用平行线性质推导\n\n**重要推论**：\n- 直角三角形的两锐角互余（和为90°）\n- 等边三角形每个角都是60°\n- 三角形至多有一个直角或钝角\n\n💡 **挑战**：四边形的内角和是多少？",
                "knowledge_points": ["三角形内角和定理", "多边形内角和"],
                "exp_gained": 15,
            }
        else:
            return {
                "content": f"欢迎来到数学世界！📐\n\n你刚问的是关于\"{message}\"的问题。\n\n**数先生能带你探索**：\n- 📊 代数（方程、不等式、函数）\n- 📐 几何（三角形、圆、平行线）\n- 📈 函数（一次函数、二次函数）\n- 📋 统计与概率\n\n**试试看**：说\"解方程 2x+5=13\"或\"画一次函数的图像\"，体验数学可视化！\n\n你想了解哪个数学知识？",
                "knowledge_points": [],
                "exp_gained": 5,
            }

    return {
        "content": f"你刚才问的是：{message}\n\n（这是演示模式响应。要启用完整 AI 对话，请在 .env 中配置 OPENAI_API_KEY）",
        "exp_gained": 5,
    }


# WebSocket 学习会话（新引擎）
@router.websocket("/ws/{subject_id}")
async def learning_websocket(websocket: WebSocket, subject_id: str, user_id: str):
    """
    学习会话 WebSocket —— 支持引导学习、自由问答、混合模式
    
    消息格式:
    -> {"type": "start_session", "mode": "guided"|"free_qa"|"hybrid"}
    <- {"type": "session_started", "session_id": "...", "mode": "..."}
    <- {"type": "question", "content": "...", "question_id": "...", "options": [...], "hint": "..."}
    -> {"type": "answer", "content": "...", "question_id": "..."}
    <- {"type": "feedback", "correct": true/false, "score": 100, "feedback": "...", "explanation": "...", "exp_gained": 15}
    -> {"type": "free_question", "content": "..."}
    <- {"type": "free_answer", "content": "...", "exp_gained": 5}
    -> {"type": "hint"}
    <- {"type": "hint", "content": "..."}
    -> {"type": "next_question"}
    <- {"type": "question", ...}
    -> {"type": "end_session"}
    <- {"type": "session_summary", "total_questions": 10, "correct_count": 8, "accuracy": 80, ...}
    """
    await websocket.accept()
    
    from src.core.learning.engine import learning_engine, LearningMode
    
    principal = get_principal_agent()
    has_api_key = bool(settings.OPENAI_API_KEY)
    session_id = None
    current_question_id = None
    
    subject_names = {"history": "历史", "physics": "物理", "math": "数学"}
    agent_names = {"history": "史博士", "physics": "物先生", "math": "数先生"}
    subject_name = subject_names.get(subject_id, subject_id)
    agent_name = agent_names.get(subject_id, subject_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")
            
            # ===== 开始会话 =====
            if msg_type == "start_session":
                mode_str = data.get("mode", "guided")
                mode_map = {
                    "guided": LearningMode.GUIDED,
                    "free_qa": LearningMode.FREE_QA,
                    "hybrid": LearningMode.HYBRID,
                }
                mode = mode_map.get(mode_str, LearningMode.GUIDED)
                
                session = learning_engine.start_session(user_id, subject_id, mode)
                session_id = session.session_id
                
                await websocket.send_json({
                    "type": "session_started",
                    "session_id": session_id,
                    "mode": mode_str,
                    "subject": subject_name,
                    "agent": agent_name,
                })
                
                # 发送欢迎消息
                if mode == LearningMode.GUIDED:
                    welcome = f"👋 欢迎来到{subject_name}课堂！我是你的{agent_name}。\n\n**引导学习模式**：我会提出问题，你来回答。每题都有反馈和解析。准备好了吗？"
                elif mode == LearningMode.FREE_QA:
                    welcome = f"👋 欢迎来到{subject_name}课堂！我是你的{agent_name}。\n\n**自由问答模式**：你可以随时向我提问，我会详细解答。"
                else:
                    welcome = f"👋 欢迎来到{subject_name}课堂！我是你的{agent_name}。\n\n**混合模式**：我会引导你学习，你也可以随时提问。"
                
                await websocket.send_json({
                    "type": "system",
                    "content": welcome,
                })
                
                # 引导模式和混合模式：自动出第一题
                if mode in (LearningMode.GUIDED, LearningMode.HYBRID):
                    question = learning_engine.get_next_question(session_id)
                    if question:
                        current_question_id = question.id
                        await send_question(websocket, question)
            
            # ===== 提交答案 =====
            elif msg_type == "answer":
                if not session_id:
                    await websocket.send_json({"type": "error", "content": "请先开始会话"})
                    continue
                
                answer_text = data.get("content", "").strip()
                if not answer_text:
                    continue
                
                result = learning_engine.submit_answer(session_id, answer_text)
                if result:
                    await websocket.send_json({
                        "type": "feedback",
                        "correct": result.correct,
                        "score": result.score,
                        "feedback": result.feedback,
                        "explanation": result.explanation,
                        "exp_gained": result.exp_gained,
                        "knowledge_reinforced": result.knowledge_reinforced,
                    })
                    current_question_id = None
            
            # ===== 下一题 =====
            elif msg_type == "next_question":
                if not session_id:
                    await websocket.send_json({"type": "error", "content": "请先开始会话"})
                    continue
                
                question = learning_engine.get_next_question(session_id)
                if question:
                    current_question_id = question.id
                    await send_question(websocket, question)
                else:
                    await websocket.send_json({
                        "type": "system",
                        "content": "🎉 太棒了！所有知识点都练习完了！",
                    })
            
            # ===== 获取提示 =====
            elif msg_type == "hint":
                if session_id:
                    hint = learning_engine.get_hint(session_id)
                    await websocket.send_json({
                        "type": "hint",
                        "content": hint,
                    })
            
            # ===== 自由提问 =====
            elif msg_type == "free_question":
                message = data.get("content", "").strip()
                if not message:
                    continue
                
                if has_api_key and subject_id in principal.agent_registry:
                    result = await principal.handle_message(user_id, message)
                    response = result["response"]
                    await websocket.send_json({
                        "type": "free_answer",
                        "content": response["content"],
                        "related_knowledge": [
                            {"title": kp.get("title", "")}
                            for kp in response.get("related_knowledge", [])
                        ],
                        "exp_gained": response.get("exp_gained", 5),
                    })
                else:
                    demo = get_demo_response(subject_id, message)
                    await websocket.send_json({
                        "type": "free_answer",
                        "content": demo["content"],
                        "related_knowledge": [
                            {"title": kp} for kp in demo.get("knowledge_points", [])
                        ],
                        "exp_gained": demo.get("exp_gained", 5),
                    })
                
                # 混合模式：回答后继续出题
                if session_id:
                    session = learning_engine.sessions.get(session_id)
                    if session and session.mode == LearningMode.HYBRID:
                        question = learning_engine.get_next_question(session_id)
                        if question:
                            current_question_id = question.id
                            await send_question(websocket, question)
            
            # ===== 结束会话 =====
            elif msg_type == "end_session":
                if session_id:
                    summary = learning_engine.end_session(session_id)
                    await websocket.send_json({
                        "type": "session_summary",
                        **summary,
                    })
                    session_id = None
            
            # ===== 完成旧任务（兼容） =====
            elif msg_type == "complete_task":
                await websocket.send_json({
                    "type": "task_completed",
                    "exp_gained": 50,
                    "achievement": None,
                })
                
    except WebSocketDisconnect:
        logger.info(f"用户 {user_id} 从 {subject_id} 学习会话断开")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "system",
                "content": f"⚠️ 发生错误：{str(e)[:100]}"
            })
        except Exception:
            pass


async def send_question(websocket: WebSocket, question):
    """发送题目"""
    type_names = {
        "choice": "选择题",
        "fill_blank": "填空题",
        "short_answer": "简答题",
        "true_false": "判断题",
    }
    
    content = f"**{type_names.get(question.type.value, '题目')}**\n\n{question.content}"
    
    if question.options:
        letters = ["A", "B", "C", "D"]
        options_text = "\n".join(
            f"{letters[i]}. {opt}" for i, opt in enumerate(question.options)
        )
        content += f"\n\n{options_text}"
    
    await websocket.send_json({
        "type": "question",
        "content": content,
        "question_id": question.id,
        "question_type": question.type.value,
        "options": question.options,
        "difficulty": question.difficulty.value,
        "knowledge_point": question.knowledge_point_title,
    })
