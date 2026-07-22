"""
Neo4j 知识图谱 - 连接层

负责:
1. Neo4j 驱动管理（单例模式）
2. 会话池管理
3. 初始化约束和索引
4. 健康检查
"""
import logging
from typing import Optional
from contextlib import contextmanager

from config.settings import settings

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Neo4j 连接管理（单例模式）"""

    _instance: Optional["Neo4jConnection"] = None
    _driver = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._driver is None:
            self._initialize_driver()

    def _initialize_driver(self):
        """初始化 Neo4j 驱动"""
        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
            # 验证连接
            self._driver.verify_connectivity()
            logger.info("✅ Neo4j 驱动初始化成功")
        except ImportError:
            logger.warning("⚠️ neo4j 包未安装，知识图谱功能不可用")
            self._driver = None
        except Exception as e:
            logger.warning(f"⚠️ Neo4j 连接失败: {e}，知识图谱功能降级")
            self._driver = None

    @property
    def is_available(self) -> bool:
        """检查 Neo4j 是否可用"""
        if self._driver is None:
            return False
        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    @contextmanager
    def session(self):
        """获取 Neo4j 会话（上下文管理器）"""
        if self._driver is None:
            raise RuntimeError("Neo4j 未初始化，请先安装并启动 Neo4j")
        session = self._driver.session(database=settings.NEO4J_DATABASE)
        try:
            yield session
        finally:
            session.close()

    def close(self):
        """关闭 Neo4j 连接"""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j 连接已关闭")

    def initialize_schema(self):
        """初始化约束和索引"""
        if not self.is_available:
            logger.warning("⚠️ Neo4j 不可用，跳过 schema 初始化")
            return

        constraints = [
            "CREATE CONSTRAINT subject_name IF NOT EXISTS FOR (s:Subject) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT event_name IF NOT EXISTS FOR (e:HistoricalEvent) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT dynasty_name IF NOT EXISTS FOR (d:Dynasty) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT knowledge_id IF NOT EXISTS FOR (k:KnowledgePoint) REQUIRE k.id IS UNIQUE",
        ]

        indexes = [
            "CREATE INDEX event_date IF NOT EXISTS FOR (e:HistoricalEvent) ON (e.start_year)",
            "CREATE INDEX person_dynasty IF NOT EXISTS FOR (p:Person) ON (p.dynasty)",
            "CREATE INDEX knowledge_subject IF NOT EXISTS FOR (k:KnowledgePoint) ON (k.subject_id)",
        ]

        with self.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint skipped: {e}")

            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    logger.debug(f"Index skipped: {e}")

        logger.info("✅ Neo4j schema 初始化完成")

    def health_check(self) -> dict:
        """健康检查"""
        if self._driver is None:
            return {"status": "unavailable", "reason": "driver_not_initialized"}

        try:
            with self.session() as session:
                result = session.run("RETURN 1 AS health")
                record = result.single()
                if record and record["health"] == 1:
                    # 获取节点和关系统计
                    stats = session.run(
                        "MATCH (n) WITH labels(n) AS label, count(n) AS cnt "
                        "RETURN label, cnt ORDER BY cnt DESC"
                    )
                    node_counts = {r["label"][0]: r["cnt"] for r in stats}

                    rel_stats = session.run(
                        "MATCH ()-[r]-() WITH type(r) AS rel_type, count(r) AS cnt "
                        "RETURN rel_type, cnt ORDER BY cnt DESC LIMIT 10"
                    )
                    rel_counts = {r["rel_type"]: r["cnt"] for r in rel_stats}

                    return {
                        "status": "healthy",
                        "nodes": node_counts,
                        "relationships": rel_counts,
                    }
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}


def get_neo4j_connection() -> Neo4jConnection:
    """获取 Neo4j 连接实例"""
    return Neo4jConnection()
