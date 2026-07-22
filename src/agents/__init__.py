"""学科 Agent 包"""
from src.agents.base_agent import SubjectAgentBase, KnowledgeBase, AgentContext, AgentResponse
from src.agents.history_agent import HistoryAgent, get_history_agent
from src.agents.physics_agent import PhysicsAgent, get_physics_agent
from src.agents.math_agent import MathAgent, get_math_agent

__all__ = [
    "SubjectAgentBase",
    "KnowledgeBase",
    "AgentContext",
    "AgentResponse",
    "HistoryAgent",
    "get_history_agent",
    "PhysicsAgent",
    "get_physics_agent",
    "MathAgent",
    "get_math_agent",
]
