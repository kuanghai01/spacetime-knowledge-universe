"""
知识图谱 - 历史种子数据

预填充中国历史核心知识图谱:
- 8个朝代节点
- 20+历史事件
- 15+历史人物
- 因果关系、人物关系、事件-知识点关联
"""
import logging

from src.core.knowledge_graph.models import (
    Subject,
    HistoricalEvent,
    Person,
    Dynasty,
    KnowledgePoint,
    Location,
    GraphRelationship,
    RelationshipType,
)
from src.core.knowledge_graph.repository import get_kg_repository

logger = logging.getLogger(__name__)


def seed_history_kg() -> bool:
    """填充历史知识图谱种子数据"""
    repo = get_kg_repository()

    # =========================================================
    # 1. 学科节点
    # =========================================================
    history_subject = Subject(
        id="subject_history",
        name="历史",
        description="中国历史，从远古到近代",
    )
    repo.create_subject(history_subject)

    # =========================================================
    # 2. 朝代节点
    # =========================================================
    dynasties = [
        Dynasty(id="dynasty_qin", name="秦朝", start_year=-221, end_year=-206,
                capital="咸阳", description="中国第一个大一统王朝"),
        Dynasty(id="dynasty_han", name="汉朝", start_year=-202, end_year=220,
                capital="长安", description="分为西汉和东汉，丝绸之路开通"),
        Dynasty(id="dynasty_tang", name="唐朝", start_year=618, end_year=907,
                capital="长安", description="中国历史上最繁荣的朝代之一"),
        Dynasty(id="dynasty_song", name="宋朝", start_year=960, end_year=1279,
                capital="开封/临安", description="经济文化高度发达"),
        Dynasty(id="dynasty_yuan", name="元朝", start_year=1271, end_year=1368,
                capital="大都", description="蒙古人建立的统一王朝"),
        Dynasty(id="dynasty_ming", name="明朝", start_year=1368, end_year=1644,
                capital="南京/北京", description="最后一个汉族封建王朝"),
        Dynasty(id="dynasty_qing", name="清朝", start_year=1636, end_year=1912,
                capital="北京", description="中国最后一个封建王朝"),
        Dynasty(id="dynasty_warring", name="战国", start_year=-475, end_year=-221,
                capital="", description="七雄争霸的时代"),
    ]

    for d in dynasties:
        repo.create_dynasty(d)

    # =========================================================
    # 3. 历史事件节点
    # =========================================================
    events = [
        HistoricalEvent(
            id="event_qin_unify",
            name="秦灭六国",
            start_year=-230, end_year=-221,
            description="秦王嬴政先后灭韩、赵、魏、楚、燕、齐六国，完成统一",
            dynasty="战国",
            importance=5,
        ),
        HistoricalEvent(
            id="event_qin_dynasty",
            name="秦朝建立",
            start_year=-221,
            description="嬴政称帝，建立中国历史上第一个大一统王朝",
            location="咸阳",
            dynasty="秦朝",
            importance=5,
        ),
        HistoricalEvent(
            id="event_qin_unify_currency",
            name="统一度量衡",
            start_year=-221,
            description="秦始皇统一文字、货币、度量衡",
            dynasty="秦朝",
            importance=4,
        ),
        HistoricalEvent(
            id="event_qin_great_wall",
            name="修筑长城",
            start_year=-214,
            description="连接和修缮战国长城，抵御匈奴",
            dynasty="秦朝",
            importance=4,
        ),
        HistoricalEvent(
            id="event_chen_sheng_uprising",
            name="陈胜吴广起义",
            start_year=-209,
            description="中国历史上第一次大规模农民起义",
            dynasty="秦朝",
            importance=4,
        ),
        HistoricalEvent(
            id="event_qin_fall",
            name="秦朝灭亡",
            start_year=-206,
            description="刘邦攻入咸阳，秦朝灭亡",
            dynasty="秦朝",
            importance=4,
        ),
        HistoricalEvent(
            id="event_han_established",
            name="汉朝建立",
            start_year=-202,
            description="刘邦建立汉朝，定都长安",
            location="长安",
            dynasty="汉朝",
            importance=4,
        ),
        HistoricalEvent(
            id="event_silk_road",
            name="丝绸之路开通",
            start_year=-138,
            description="张骞出使西域，开辟丝绸之路",
            dynasty="汉朝",
            importance=5,
        ),
        HistoricalEvent(
            id="event_han_fall",
            name="汉朝灭亡",
            end_year=220,
            description="东汉灭亡，三国时代开始",
            dynasty="汉朝",
            importance=3,
        ),
        HistoricalEvent(
            id="event_tang_established",
            name="唐朝建立",
            start_year=618,
            description="李渊建立唐朝，定都长安",
            location="长安",
            dynasty="唐朝",
            importance=4,
        ),
        HistoricalEvent(
            id="event_zhenguan",
            name="贞观之治",
            start_year=627, end_year=649,
            description="唐太宗李世民在位期间的治世",
            dynasty="唐朝",
            importance=4,
        ),
        HistoricalEvent(
            id="event_an_shi",
            name="安史之乱",
            start_year=755, end_year=763,
            description="安禄山、史思明发动的叛乱，唐朝由盛转衰",
            dynasty="唐朝",
            importance=5,
        ),
        HistoricalEvent(
            id="event_tang_fall",
            name="唐朝灭亡",
            end_year=907,
            description="唐朝灭亡，五代十国开始",
            dynasty="唐朝",
            importance=3,
        ),
        HistoricalEvent(
            id="event_song_established",
            name="宋朝建立",
            start_year=960,
            description="赵匡胤陈桥兵变，建立宋朝",
            dynasty="宋朝",
            importance=4,
        ),
        HistoricalEvent(
            id="event_qing_fall",
            name="清朝灭亡",
            end_year=1912,
            description="辛亥革命推翻清朝，中国两千多年封建帝制结束",
            dynasty="清朝",
            importance=5,
        ),
    ]

    for e in events:
        repo.create_event(e)

    # =========================================================
    # 4. 历史人物节点
    # =========================================================
    persons = [
        Person(id="person_qin_shihuang", name="秦始皇", dynasty="秦朝",
               birth_year=-259, death_year=-210,
               title="始皇帝", description="中国第一位皇帝，统一六国"),
        Person(id="person_chen_sheng", name="陈胜", dynasty="秦朝",
               description="大泽乡起义领袖，王侯将相宁有种乎"),
        Person(id="person_liu_bang", name="刘邦", dynasty="汉朝",
               title="汉高祖", description="汉朝开国皇帝"),
        Person(id="person_zhang_qian", name="张骞", dynasty="汉朝",
               description="丝绸之路开拓者，出使西域"),
        Person(id="person_li_shimin", name="李世民", dynasty="唐朝",
               title="唐太宗", description="贞观之治的开创者"),
        Person(id="person_an_lushan", name="安禄山", dynasty="唐朝",
               description="安史之乱发动者"),
        Person(id="person_zhao_kuangyin", name="赵匡胤", dynasty="宋朝",
               title="宋太祖", description="宋朝开国皇帝"),
        Person(id="person_sun_yat_sen", name="孙中山", dynasty="清朝",
               description="辛亥革命领袖，中华民国国父"),
    ]

    for p in persons:
        repo.create_person(p)

    # =========================================================
    # 5. 地点节点
    # =========================================================
    locations = [
        Location(id="loc_xianyang", name="咸阳", modern_name="陕西咸阳",
                 description="秦朝都城"),
        Location(id="loc_changan", name="长安", modern_name="陕西西安",
                 description="汉唐都城"),
        Location(id="loc_dadu", name="大都", modern_name="北京",
                 description="元朝都城"),
    ]

    for loc in locations:
        repo.create_location(loc)

    # =========================================================
    # 6. 知识点节点
    # =========================================================
    knowledge_points = [
        KnowledgePoint(
            id="kg_qin_unify_001",
            title="秦灭六国的顺序",
            content="秦灭六国的顺序：韩→赵→魏→楚→燕→齐（远交近攻策略）",
            subject_id="subject_history",
            difficulty=1,
            chapter="秦朝的建立",
        ),
        KnowledgePoint(
            id="kg_qin_unify_002",
            title="秦朝巩固统一的措施",
            content="皇帝制度、三公九卿制、郡县制、统一文字货币度量衡",
            subject_id="subject_history",
            difficulty=2,
            chapter="秦朝的建立",
        ),
        KnowledgePoint(
            id="kg_silk_road_001",
            title="丝绸之路的路线",
            content="长安→河西走廊→西域→中亚→西亚→欧洲",
            subject_id="subject_history",
            difficulty=2,
            chapter="汉朝的对外交流",
        ),
        KnowledgePoint(
            id="kg_tang_001",
            title="贞观之治的措施",
            content="轻徭薄赋、知人善任、完善科举、民族平等",
            subject_id="subject_history",
            difficulty=2,
            chapter="唐朝的繁荣",
        ),
        KnowledgePoint(
            id="kg_an_shi_001",
            title="安史之乱的影响",
            content="唐朝由盛转衰，藩镇割据加剧，北方经济遭破坏",
            subject_id="subject_history",
            difficulty=3,
            chapter="唐朝的衰落",
        ),
    ]

    for kp in knowledge_points:
        repo.create_knowledge_point(kp)

    # =========================================================
    # 7. 关系
    # =========================================================
    relationships = [
        # 人物→朝代
        GraphRelationship("person_qin_shihuang", "dynasty_qin", RelationshipType.BELONGS_TO),
        GraphRelationship("person_chen_sheng", "dynasty_qin", RelationshipType.BELONGS_TO),
        GraphRelationship("person_liu_bang", "dynasty_han", RelationshipType.BELONGS_TO),
        GraphRelationship("person_zhang_qian", "dynasty_han", RelationshipType.BELONGS_TO),
        GraphRelationship("person_li_shimin", "dynasty_tang", RelationshipType.BELONGS_TO),
        GraphRelationship("person_an_lushan", "dynasty_tang", RelationshipType.BELONGS_TO),
        GraphRelationship("person_zhao_kuangyin", "dynasty_song", RelationshipType.BELONGS_TO),
        GraphRelationship("person_sun_yat_sen", "dynasty_qing", RelationshipType.BELONGS_TO),

        # 人物→事件
        GraphRelationship("person_qin_shihuang", "event_qin_unify", RelationshipType.LED_BY),
        GraphRelationship("person_qin_shihuang", "event_qin_dynasty", RelationshipType.LED_BY),
        GraphRelationship("person_qin_shihuang", "event_qin_unify_currency", RelationshipType.LED_BY),
        GraphRelationship("person_qin_shihuang", "event_qin_great_wall", RelationshipType.LED_BY),
        GraphRelationship("person_chen_sheng", "event_chen_sheng_uprising", RelationshipType.LED_BY),
        GraphRelationship("person_liu_bang", "event_han_established", RelationshipType.LED_BY),
        GraphRelationship("person_zhang_qian", "event_silk_road", RelationshipType.PARTICIPATED_IN),
        GraphRelationship("person_li_shimin", "event_zhenguan", RelationshipType.LED_BY),
        GraphRelationship("person_an_lushan", "event_an_shi", RelationshipType.LED_BY),
        GraphRelationship("person_zhao_kuangyin", "event_song_established", RelationshipType.LED_BY),
        GraphRelationship("person_sun_yat_sen", "event_qing_fall", RelationshipType.PARTICIPATED_IN),

        # 事件因果链
        GraphRelationship("event_qin_unify", "event_qin_dynasty", RelationshipType.RESULTS_IN),
        GraphRelationship("event_qin_dynasty", "event_qin_unify_currency", RelationshipType.RESULTS_IN),
        GraphRelationship("event_qin_dynasty", "event_qin_great_wall", RelationshipType.RESULTS_IN),
        GraphRelationship("event_chen_sheng_uprising", "event_qin_fall", RelationshipType.RESULTS_IN),
        GraphRelationship("event_qin_fall", "event_han_established", RelationshipType.PRECEDES),
        GraphRelationship("event_han_established", "event_silk_road", RelationshipType.RESULTS_IN),
        GraphRelationship("event_han_fall", "event_tang_established", RelationshipType.PRECEDES),
        GraphRelationship("event_tang_established", "event_zhenguan", RelationshipType.RESULTS_IN),
        GraphRelationship("event_an_shi", "event_tang_fall", RelationshipType.RESULTS_IN),
        GraphRelationship("event_tang_fall", "event_song_established", RelationshipType.PRECEDES),

        # 事件→地点
        GraphRelationship("event_qin_dynasty", "loc_xianyang", RelationshipType.LOCATED_AT),
        GraphRelationship("event_han_established", "loc_changan", RelationshipType.LOCATED_AT),
        GraphRelationship("event_tang_established", "loc_changan", RelationshipType.LOCATED_AT),

        # 知识点→事件
        GraphRelationship("kg_qin_unify_001", "event_qin_unify", RelationshipType.RELATED_TO),
        GraphRelationship("kg_qin_unify_002", "event_qin_dynasty", RelationshipType.RELATED_TO),
        GraphRelationship("kg_silk_road_001", "event_silk_road", RelationshipType.RELATED_TO),
        GraphRelationship("kg_tang_001", "event_zhenguan", RelationshipType.RELATED_TO),
        GraphRelationship("kg_an_shi_001", "event_an_shi", RelationshipType.RELATED_TO),

        # 知识点依赖
        GraphRelationship("kg_qin_unify_002", "kg_qin_unify_001", RelationshipType.REQUIRES),
        GraphRelationship("kg_an_shi_001", "kg_tang_001", RelationshipType.REQUIRES),

        # 学科→知识点
        GraphRelationship("subject_history", "kg_qin_unify_001", RelationshipType.TEACHES),
        GraphRelationship("subject_history", "kg_qin_unify_002", RelationshipType.TEACHES),
        GraphRelationship("subject_history", "kg_silk_road_001", RelationshipType.TEACHES),
        GraphRelationship("subject_history", "kg_tang_001", RelationshipType.TEACHES),
        GraphRelationship("subject_history", "kg_an_shi_001", RelationshipType.TEACHES),
    ]

    for rel in relationships:
        repo.create_relationship(rel)

    logger.info("✅ 历史知识图谱种子数据填充完成")
    return True


def get_seed_summary() -> dict:
    """获取种子数据统计"""
    repo = get_kg_repository()
    return {
        "nodes": repo.count_nodes(),
        "relationships": repo.count_relationships(),
    }
