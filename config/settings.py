"""
时空知识宇宙 - 配置管理
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "时空知识宇宙"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # API 配置
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/spacetime"
    
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Milvus 向量数据库
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    
    # Neo4j 知识图谱
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # OpenAI 配置
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    
    # 游戏化配置
    BASE_EXP_PER_KNOWLEDGE: int = 10
    MAX_STREAK_BONUS: float = 1.0
    FIRST_MASTERY_BONUS: float = 1.5
    PERFECT_ANSWER_BONUS: float = 1.2
    CROSS_SUBJECT_BONUS: float = 1.3
    
    # 支持的学科
    AVAILABLE_SUBJECTS: list[str] = ["history", "physics", "math", "chemistry"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
