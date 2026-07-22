"""
学习引擎 —— 引导式学习 + 自由问答 + 混合模式
核心逻辑：系统主动提问 → 学生回答 → 智能反馈 → 自适应下一题
"""
import random
import logging
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    CHOICE = "choice"           # 选择题
    FILL_BLANK = "fill_blank"   # 填空题
    SHORT_ANSWER = "short_answer"  # 简答题
    TRUE_FALSE = "true_false"   # 判断题


class LearningMode(Enum):
    GUIDED = "guided"           # 引导学习
    FREE_QA = "free_qa"         # 自由问答
    HYBRID = "hybrid"           # 混合模式


class DifficultyLevel(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3


@dataclass
class Question:
    """题目"""
    id: str
    type: QuestionType
    content: str                    # 题目内容
    correct_answer: str             # 正确答案
    options: list[str] = field(default_factory=list)  # 选择题选项
    explanation: str = ""           # 解析
    knowledge_point_id: str = ""    # 关联知识点ID
    knowledge_point_title: str = "" # 关联知识点标题
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    hint: str = ""                  # 提示
    subject: str = ""               # 学科


@dataclass
class AnswerResult:
    """答题结果"""
    correct: bool
    score: float                    # 0-100
    feedback: str                   # 反馈文本
    explanation: str = ""           # 详细解析
    exp_gained: int = 0             # 获得经验
    knowledge_reinforced: list[str] = field(default_factory=list)  # 强化的知识点


@dataclass
class LearningSession:
    """学习会话"""
    session_id: str
    user_id: str
    subject: str
    mode: LearningMode
    current_question: Optional[Question] = None
    question_history: list[dict] = field(default_factory=list)
    correct_count: int = 0
    total_count: int = 0
    total_score: float = 0
    current_difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    start_time: str = ""
    is_active: bool = True


class QuestionBank:
    """题库生成器 —— 从知识库自动生成题目"""
    
    def __init__(self):
        self._question_templates = {
            "history": {
                QuestionType.CHOICE: [
                    "{title}的主要内容是什么？",
                    "关于{title}，下列说法正确的是？",
                    "{title}发生在哪一时期？",
                ],
                QuestionType.TRUE_FALSE: [
                    "{title}是正确的。",
                    "{content}，这个说法对吗？",
                ],
                QuestionType.FILL_BLANK: [
                    "{title}的核心是____。",
                    "____是{title}的关键。",
                ],
                QuestionType.SHORT_ANSWER: [
                    "请简述{title}。",
                    "{title}有什么重要意义？",
                    "请解释什么是{title}。",
                ],
            },
            "physics": {
                QuestionType.CHOICE: [
                    "关于{title}，下列说法正确的是？",
                    "{title}的原理是什么？",
                    "下列哪个现象与{title}有关？",
                ],
                QuestionType.TRUE_FALSE: [
                    "{title}是正确的。",
                    "{content}，这个说法对吗？",
                ],
                QuestionType.FILL_BLANK: [
                    "{title}的公式是____。",
                    "____是{title}的关键概念。",
                ],
                QuestionType.SHORT_ANSWER: [
                    "请解释{title}。",
                    "{title}在生活中的应用有哪些？",
                    "请简述{title}的原理。",
                ],
            },
            "math": {
                QuestionType.CHOICE: [
                    "关于{title}，下列说法正确的是？",
                    "{title}的正确解法是？",
                    "下列哪个是{title}？",
                ],
                QuestionType.TRUE_FALSE: [
                    "{title}是正确的。",
                    "{content}，这个说法对吗？",
                ],
                QuestionType.FILL_BLANK: [
                    "{title}的结果是____。",
                    "____是{title}的关键步骤。",
                ],
                QuestionType.SHORT_ANSWER: [
                    "请解释{title}。",
                    "请举例说明{title}。",
                    "{title}的解题步骤是什么？",
                ],
            },
        }
    
    def generate_questions(self, knowledge_points: list[dict], subject: str, 
                          difficulty: DifficultyLevel = None, count: int = 5) -> list[Question]:
        """从知识点生成题目"""
        questions = []
        templates = self._question_templates.get(subject, self._question_templates["history"])
        
        for i, kp in enumerate(knowledge_points[:count]):
            # 根据难度选择题型
            if difficulty == DifficultyLevel.EASY:
                q_type = random.choice([QuestionType.CHOICE, QuestionType.TRUE_FALSE])
            elif difficulty == DifficultyLevel.MEDIUM:
                q_type = random.choice([QuestionType.CHOICE, QuestionType.FILL_BLANK, QuestionType.TRUE_FALSE])
            else:
                q_type = random.choice([QuestionType.FILL_BLANK, QuestionType.SHORT_ANSWER, QuestionType.CHOICE])
            
            template = random.choice(templates.get(q_type, templates[QuestionType.SHORT_ANSWER]))
            
            # 生成选项（选择题）
            options = []
            if q_type == QuestionType.CHOICE:
                # 从知识点内容中提取关键信息作为正确选项
                correct = self._extract_key_sentence(kp.get("content", ""), kp.get("title", ""))
                options = self._generate_distractors(kp, knowledge_points, correct)
            
            # 生成正确答案
            correct_answer = self._generate_correct_answer(kp, q_type)
            
            # 生成解析
            explanation = self._generate_explanation(kp)
            
            # 生成提示
            hint = self._generate_hint(kp)
            
            q = Question(
                id=f"q_{kp['id']}_{i}",
                type=q_type,
                content=template.format(title=kp.get("title", ""), content=kp.get("content", "")[:100]),
                correct_answer=correct_answer,
                options=options,
                explanation=explanation,
                knowledge_point_id=kp.get("id", ""),
                knowledge_point_title=kp.get("title", ""),
                difficulty=difficulty or DifficultyLevel.MEDIUM,
                hint=hint,
                subject=subject,
            )
            questions.append(q)
        
        random.shuffle(questions)
        return questions
    
    def _extract_key_sentence(self, content: str, title: str) -> str:
        """从内容中提取关键句"""
        sentences = content.split("。")
        if sentences:
            # 找包含标题关键词的句子
            for s in sentences:
                if any(kw in s for kw in title[:4]):
                    return s.strip()[:50]
            return sentences[0][:50]
        return content[:50]
    
    def _generate_distractors(self, kp: dict, all_kps: list[dict], correct: str) -> list[str]:
        """生成干扰项"""
        options = [correct] if correct else [kp.get("title", "")]
        
        # 从其他知识点找干扰项
        for other in all_kps:
            if other["id"] != kp["id"] and len(options) < 4:
                distractor = self._extract_key_sentence(other.get("content", ""), other.get("title", ""))
                if distractor and distractor not in options:
                    options.append(distractor[:50])
        
        # 填充到4个选项
        while len(options) < 4:
            options.append(f"以上都不是（选项{len(options)+1}）")
        
        random.shuffle(options)
        return options[:4]
    
    def _generate_correct_answer(self, kp: dict, q_type: QuestionType) -> str:
        """生成正确答案"""
        content = kp.get("content", "")
        title = kp.get("title", "")
        
        if q_type == QuestionType.TRUE_FALSE:
            return "正确"
        elif q_type == QuestionType.CHOICE:
            return self._extract_key_sentence(content, title)
        elif q_type == QuestionType.FILL_BLANK:
            # 提取关键词
            return title
        else:
            # 简答题：返回内容摘要
            return content[:100]
    
    def _generate_explanation(self, kp: dict) -> str:
        """生成解析"""
        return f"📚 **{kp.get('title', '')}**\n\n{kp.get('content', '')}"
    
    def _generate_hint(self, kp: dict) -> str:
        """生成提示"""
        tags = kp.get("tags", [])
        if tags:
            return f"💡 提示：关注关键词「{tags[0]}」"
        return f"💡 提示：联系{kp.get('title', '')}的核心内容"


class AnswerEvaluator:
    """答案评估器"""
    
    def evaluate(self, question: Question, user_answer: str) -> AnswerResult:
        """评估学生答案"""
        user_answer = user_answer.strip()
        
        if question.type == QuestionType.CHOICE:
            return self._evaluate_choice(question, user_answer)
        elif question.type == QuestionType.TRUE_FALSE:
            return self._evaluate_true_false(question, user_answer)
        elif question.type == QuestionType.FILL_BLANK:
            return self._evaluate_fill_blank(question, user_answer)
        else:
            return self._evaluate_short_answer(question, user_answer)
    
    def _evaluate_choice(self, question: Question, user_answer: str) -> AnswerResult:
        """评估选择题"""
        # 支持 A/B/C/D 或 1/2/3/4 或直接输入答案
        correct_idx = -1
        for i, opt in enumerate(question.options):
            if opt == question.correct_answer:
                correct_idx = i
                break
        
        answer_map = {"A": 0, "B": 1, "C": 2, "D": 3, "1": 0, "2": 1, "3": 2, "4": 3}
        user_idx = answer_map.get(user_answer.upper(), -1)
        
        # 也支持直接输入选项内容
        if user_idx == -1:
            for i, opt in enumerate(question.options):
                if user_answer in opt or opt in user_answer:
                    user_idx = i
                    break
        
        correct = (user_idx == correct_idx and user_idx >= 0)
        
        if correct:
            return AnswerResult(
                correct=True,
                score=100,
                feedback="✅ **回答正确！** 太棒了！",
                explanation=question.explanation,
                exp_gained=15,
                knowledge_reinforced=[question.knowledge_point_id],
            )
        else:
            correct_letter = chr(65 + correct_idx) if 0 <= correct_idx < 4 else "?"
            return AnswerResult(
                correct=False,
                score=0,
                feedback=f"❌ **回答错误。** 正确答案是 **{correct_letter}**。",
                explanation=question.explanation,
                exp_gained=5,
            )
    
    def _evaluate_true_false(self, question: Question, user_answer: str) -> AnswerResult:
        """评估判断题"""
        positive = ["对", "正确", "是", "yes", "true", "√", "对的对的"]
        negative = ["错", "错误", "否", "no", "false", "×", "不对"]
        
        user_positive = any(p in user_answer for p in positive)
        user_negative = any(n in user_answer for n in negative)
        correct_positive = question.correct_answer == "正确"
        
        correct = (user_positive and correct_positive) or (user_negative and not correct_positive)
        
        if correct:
            return AnswerResult(
                correct=True,
                score=100,
                feedback="✅ **判断正确！** 很好！",
                explanation=question.explanation,
                exp_gained=10,
                knowledge_reinforced=[question.knowledge_point_id],
            )
        else:
            return AnswerResult(
                correct=False,
                score=0,
                feedback=f"❌ **判断错误。** 正确答案是「{question.correct_answer}」。",
                explanation=question.explanation,
                exp_gained=5,
            )
    
    def _evaluate_fill_blank(self, question: Question, user_answer: str) -> AnswerResult:
        """评估填空题"""
        correct_answer = question.correct_answer.lower()
        user = user_answer.lower()
        
        # 精确匹配
        if user == correct_answer:
            return AnswerResult(
                correct=True,
                score=100,
                feedback="✅ **完全正确！** 完美！",
                explanation=question.explanation,
                exp_gained=20,
                knowledge_reinforced=[question.knowledge_point_id],
            )
        
        # 关键词匹配
        correct_keywords = set(correct_answer)
        user_keywords = set(user)
        overlap = len(correct_keywords & user_keywords) / max(len(correct_keywords), 1)
        
        if overlap > 0.6:
            return AnswerResult(
                correct=True,
                score=70,
                feedback=f"✅ **基本正确！** 你的答案很接近了。更准确的答案是「{correct_answer}」。",
                explanation=question.explanation,
                exp_gained=12,
                knowledge_reinforced=[question.knowledge_point_id],
            )
        
        return AnswerResult(
            correct=False,
            score=0,
            feedback=f"❌ **答案不正确。** 正确答案是「{correct_answer}」。",
            explanation=question.explanation,
            exp_gained=5,
        )
    
    def _evaluate_short_answer(self, question: Question, user_answer: str) -> AnswerResult:
        """评估简答题（基于关键词匹配）"""
        correct_content = question.correct_answer.lower()
        user = user_answer.lower()
        
        # 提取关键词（从正确答案中）
        import re
        correct_keywords = set(re.findall(r'[\u4e00-\u9fff]+', correct_content))
        user_keywords = set(re.findall(r'[\u4e00-\u9fff]+', user))
        
        if not correct_keywords:
            # 无法提取关键词，只要有内容就给分
            if len(user_answer) > 10:
                return AnswerResult(
                    correct=True,
                    score=60,
                    feedback="✅ **已收到你的回答。** 建议对照解析进一步完善。",
                    explanation=question.explanation,
                    exp_gained=10,
                )
            return AnswerResult(
                correct=False,
                score=0,
                feedback="❌ **答案太短了。** 请尝试给出更完整的回答。",
                explanation=question.explanation,
                exp_gained=5,
            )
        
        # 计算关键词覆盖率
        overlap = len(correct_keywords & user_keywords)
        coverage = overlap / len(correct_keywords)
        
        if coverage >= 0.5:
            return AnswerResult(
                correct=True,
                score=60 + int(coverage * 40),
                feedback=f"✅ **回答正确！** 你提到了{overlap}个关键概念，覆盖率{int(coverage*100)}%。",
                explanation=question.explanation,
                exp_gained=15 + int(coverage * 10),
                knowledge_reinforced=[question.knowledge_point_id],
            )
        else:
            return AnswerResult(
                correct=False,
                score=int(coverage * 50),
                feedback=f"⚠️ **部分正确。** 你提到了{overlap}个关键概念，还需要补充。",
                explanation=question.explanation,
                exp_gained=5,
            )


class LearningEngine:
    """学习引擎 —— 管理学习会话和出题逻辑"""
    
    def __init__(self):
        self.question_bank = QuestionBank()
        self.evaluator = AnswerEvaluator()
        self.sessions: dict[str, LearningSession] = {}
        self._knowledge_cache: dict[str, list[dict]] = {}
    
    def start_session(self, user_id: str, subject: str, 
                     mode: LearningMode = LearningMode.GUIDED) -> LearningSession:
        """开始学习会话"""
        import uuid
        from datetime import datetime
        
        session = LearningSession(
            session_id=str(uuid.uuid4())[:8],
            user_id=user_id,
            subject=subject,
            mode=mode,
            start_time=datetime.now().isoformat(),
        )
        self.sessions[session.session_id] = session
        
        # 加载知识点
        knowledge = self._load_knowledge(subject)
        self._knowledge_cache[subject] = knowledge
        
        logger.info(f"学习会话开始: {session.session_id} | 用户: {user_id} | 学科: {subject} | 模式: {mode.value}")
        return session
    
    def get_next_question(self, session_id: str) -> Optional[Question]:
        """获取下一题"""
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return None
        
        knowledge = self._knowledge_cache.get(session.subject, [])
        if not knowledge:
            return None
        
        # 根据答题表现调整难度
        difficulty = self._adapt_difficulty(session)
        
        # 选择未使用过的知识点
        used_kp_ids = [q.get("kp_id") for q in session.question_history]
        available = [kp for kp in knowledge if kp.get("id") not in used_kp_ids]
        
        if not available:
            # 所有知识点都用过了，重置
            available = knowledge
        
        # 生成题目
        questions = self.question_bank.generate_questions(
            available, session.subject, difficulty, count=1
        )
        
        if questions:
            session.current_question = questions[0]
            return questions[0]
        return None
    
    def submit_answer(self, session_id: str, answer: str) -> Optional[AnswerResult]:
        """提交答案"""
        session = self.sessions.get(session_id)
        if not session or not session.current_question:
            return None
        
        question = session.current_question
        result = self.evaluator.evaluate(question, answer)
        
        # 更新会话状态
        session.total_count += 1
        session.total_score += result.score
        if result.correct:
            session.correct_count += 1
        
        session.question_history.append({
            "question_id": question.id,
            "kp_id": question.knowledge_point_id,
            "user_answer": answer,
            "correct": result.correct,
            "score": result.score,
        })
        
        # 清除当前题目
        session.current_question = None
        
        return result
    
    def get_hint(self, session_id: str) -> str:
        """获取提示"""
        session = self.sessions.get(session_id)
        if session and session.current_question:
            return session.current_question.hint
        return "暂无提示"
    
    def get_session_summary(self, session_id: str) -> dict:
        """获取会话总结"""
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        avg_score = session.total_score / max(session.total_count, 1)
        accuracy = session.correct_count / max(session.total_count, 1)
        
        return {
            "session_id": session.session_id,
            "subject": session.subject,
            "mode": session.mode.value,
            "total_questions": session.total_count,
            "correct_count": session.correct_count,
            "accuracy": round(accuracy * 100, 1),
            "average_score": round(avg_score, 1),
            "exp_gained": session.total_count * 10 + session.correct_count * 5,
            "duration_minutes": 0,  # TODO: 计算时长
        }
    
    def end_session(self, session_id: str) -> dict:
        """结束学习会话"""
        session = self.sessions.get(session_id)
        if session:
            session.is_active = False
        return self.get_session_summary(session_id)
    
    def _adapt_difficulty(self, session: LearningSession) -> DifficultyLevel:
        """自适应难度调整"""
        if session.total_count < 2:
            return DifficultyLevel.EASY
        
        accuracy = session.correct_count / session.total_count
        
        if accuracy >= 0.8:
            # 答对率高，提升难度
            if session.current_difficulty == DifficultyLevel.EASY:
                return DifficultyLevel.MEDIUM
            elif session.current_difficulty == DifficultyLevel.MEDIUM:
                return DifficultyLevel.HARD
        elif accuracy < 0.4:
            # 答对率低，降低难度
            if session.current_difficulty == DifficultyLevel.HARD:
                return DifficultyLevel.MEDIUM
            elif session.current_difficulty == DifficultyLevel.MEDIUM:
                return DifficultyLevel.EASY
        
        return session.current_difficulty
    
    def _load_knowledge(self, subject: str) -> list[dict]:
        """加载知识点"""
        try:
            if subject == "history":
                from src.data.history_data import ALL_HISTORY_KNOWLEDGE
                return ALL_HISTORY_KNOWLEDGE
            elif subject == "math":
                from src.data.math_data import ALL_MATH_KNOWLEDGE
                return ALL_MATH_KNOWLEDGE
            elif subject == "physics":
                from src.data.physics_data import ALL_PHYSICS_KNOWLEDGE
                return ALL_PHYSICS_KNOWLEDGE
        except ImportError as e:
            logger.warning(f"加载知识点失败: {e}")
        return []


# 全局学习引擎实例
learning_engine = LearningEngine()
