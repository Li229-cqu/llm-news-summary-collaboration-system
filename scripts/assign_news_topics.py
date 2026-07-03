#!/usr/bin/env python3
"""Timeline 事件脉络 — 候选话题 dry-run 归类脚本。

根据预定义的候选话题关键词列表，扫描 news 表中所有未归类新闻，
预览每个话题可以匹配到哪些新闻。不修改任何数据库数据。

Usage:
    python scripts/assign_news_topics.py --dry-run    # 默认模式：预览匹配结果
    python scripts/assign_news_topics.py --apply      # 尚未实现：输出提示信息
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any

# ── 数据库配置（从环境变量读取，与 backend/.env 保持一致） ──
DB_CONFIG: dict[str, Any] = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "llm_news_user"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "llm_news_system"),
    "charset": "utf8mb4",
}

# ═══════════════════════════════════════════════════════════════════════
# 候选话题配置
# ═══════════════════════════════════════════════════════════════════════

TOPIC_CANDIDATES: list[dict[str, Any]] = [
    # ── 优先入库（前10）──
    {
        "topic_name": "美加墨世界杯赛事与热点追踪",
        "category": "体育",
        "heat_score": 98,
        "summary": "围绕美加墨世界杯淘汰赛阶段的焦点对决、晋级形势和赛事热点，梳理关键比赛进展。",
        "min_score": 2,
        "keywords": [
            # 精确赛事词（单个即可命中但需 ≥2）
            "世界杯",
            "美加墨",
            "淘汰赛",
            "16强",
            "32强",
            "点球大战",
            "队史首进",
            "FIFA",
            # 辅助词（需组合命中才够 min_score=2）
            "晋级",
            "绝杀",
            "巴西队",
            "德国队",
            "日本队",
            "巴拉圭队",
            "桑巴军团",
            "加拿大队",
            "荷兰队",
            "摩洛哥",
            "门将",
            "足球",
            "补时",
        ],
        "exclude_keywords": [
            "女排", "网球", "温网", "WTT", "田径",
            "通胀", "枪击", "商务部", "管制升级",
            "贸易", "外汇", "日元", "防卫",
            "军事", "军演", "油价", "央行",
        ],
    },
    {
        "topic_name": "委内瑞拉强震灾害与国际救援行动",
        "category": "国际",
        "heat_score": 95,
        "summary": "追踪委内瑞拉强震后的灾情发展、死亡人数攀升、国际社会援助响应及华侨华人捐赠行动。",
        "min_score": 2,
        "keywords": [
            # 精确词（单命中即可，但需 min_score=2）
            "委内瑞拉",
            "加拉加斯",
            "华侨华人",
            "欧盟援助",
            "中资企业",
            # 辅助词（需组合命中）
            "地震",
            "强震",
            "遇难",
            "死亡人数",
            "救援",
            "救灾",
            "震感",
            "捐赠",
        ],
        "exclude_keywords": [
            "死亡威胁",
            "韩国队",
            "洪明甫",
            "足球",
            "机场嘘声",
        ],
    },
    {
        "topic_name": "中国共产党成立105周年专题报道",
        "category": "时政",
        "heat_score": 92,
        "summary": "围绕七一建党105周年系列活动，包括党员统计公报、纪念章颁发、主题音乐会等集中报道。",
        "min_score": 1,
        "keywords": [
            "105周年",
            "七一勋章",
            "光荣在党",
            "党员总数",
            "统计公报",
            "中国共产党成立",
            "庆祝中国共产",
            "基层党组织",
            "纪念章",
            "党建思想",
            "建党",
            "七一",
            "党组织",
        ],
        "exclude_keywords": [
            "反腐", "受贿", "审查调查", "提起公诉",
        ],
    },
    {
        "topic_name": "国家网络安全宣传周与数字安全治理",
        "category": "科技",
        "heat_score": 90,
        "summary": "围绕国家网络安全宣传周系列活动，涵盖博览会、主题论坛、校园日、攻防演练等数字安全治理成果。",
        "min_score": 1,
        "keywords": [
            "网络安全宣传周",
            "网安周",
            "网络安全博览会",
            "国家网络安全",
            "个人信息保护",
            "网络诈骗",
            "网络谣言",
            "数字安全",
            "网络治理",
            "网安博览会",
            "网络安全知识",
            "网络安全产业",
            "网络安全",
            "信息安全",
            "数据安全",
            "安全周",
        ],
        "exclude_keywords": [
            "车联网", "新能源汽车", "智能驾驶", "充电桩",
        ],
    },
    {
        "topic_name": "全国强降雨天气与防汛防灾应对",
        "category": "社会",
        "heat_score": 86,
        "summary": "追踪2026年夏季云贵高原至长江中下游持续强降雨、华南华北高温闷热等极端天气过程及各地应对。",
        "min_score": 1,
        "keywords": [
            "强降雨", "暴雨", "防汛", "天气预警",
            "云贵高原", "长江中下游", "雷阵雨",
            "高温闷热", "雨势较强", "防洪",
            "华北雷雨", "降水", "黄淮", "华南",
            "防灾", "气象",
        ],
        "exclude_keywords": [
            "桨板", "攀岩", "健身大赛", "世界杯",
        ],
    },
    {
        "topic_name": "美伊关系紧张与中东地缘博弈",
        "category": "国际",
        "heat_score": 88,
        "summary": "围绕美国与伊朗在多哈的核谈判僵局、以色列对伊朗的军事警告、中东地区力量博弈等关键节点。",
        "min_score": 1,
        "keywords": [
            "伊朗", "多哈谈判", "以色列", "中东",
            "核问题", "以防长", "美军",
            "波斯", "万斯威胁",
            "谈判", "武力", "制裁",
        ],
        "exclude_keywords": [
            "地震", "委内瑞拉", "世界杯", "足球",
        ],
    },
    {
        "topic_name": "特朗普系列司法裁决与政治影响",
        "category": "国际",
        "heat_score": 85,
        "summary": "追踪特朗普涉及的性侵案上诉被驳回、最高法院人事裁决、内阁提名、对外关税威胁等政治司法事件。",
        "min_score": 1,
        "keywords": [
            "特朗普", "最高法院", "裁定",
            "联邦贸易委员会", "劳工部长",
            "性侵案", "美国总统",
            "博尔顿", "共和党",
            "提名", "关税",
        ],
        "exclude_keywords": [
            "金民锡", "韩国", "韩德洙",
        ],
    },
    {
        "topic_name": "高铁新线开通与铁路交通建设进展",
        "category": "社会",
        "heat_score": 83,
        "summary": "追踪西十高铁开通运营、青藏铁路通车20年、北京市郊铁路提升工程等重大铁路交通建设里程碑。",
        "min_score": 2,
        "keywords": [
            # 精确交通词
            "高铁",
            "铁路",
            "西十",
            "青藏铁路",
            "市郊铁路",
            "轨道交通",
            "动车",
            "城际",
            "火车站",
            "站台",
            # 辅助词
            "开通运营",
            "交通建设",
            "西安至十堰",
            "投运",
            "线路",
        ],
        "exclude_keywords": [
            "网络安全", "网安周", "校园", "音乐会",
            "文化", "旅游", "博览会",
        ],
    },
    {
        "topic_name": "制造业PMI与宏观经济数据观察",
        "category": "财经",
        "heat_score": 82,
        "summary": "围绕6月制造业PMI(50.3%)、工业企业利润、经济体制改革及十五五规划解读等关键宏观数据报道。",
        "min_score": 1,
        "keywords": [
            "制造业PMI", "PMI", "采购经理指数",
            "工业利润", "规模以上工业",
            "宏观经济", "经济数据",
            "统计局", "经济体制",
            "十五五", "GDP",
            "制造业",
        ],
        "exclude_keywords": [
            "人力资源", "人社部", "试点工作",
        ],
    },
    {
        "topic_name": "中欧贸易投资磋商与双边经贸关系",
        "category": "财经",
        "heat_score": 80,
        "summary": "围绕中欧贸易投资磋商机制正式成立、首次会议召开、亚欧博览会及跨境电商合作等双边经贸进展。",
        "min_score": 2,
        "keywords": [
            # 精确经贸词
            "中欧",
            "贸易投资磋商",
            "经贸",
            "磋商机制",
            "联合声明",
            "亚欧博览会",
            "跨境电商",
            "出口通道",
            "塔城",
            "喀山",
            "中亚",
            "双边贸易",
            "投资合作",
            "中欧班列",
            # 辅助词
            "贸易",
            "投资",
        ],
        "exclude_keywords": [
            "军事", "军演", "俄乌", "袭击",
            "导弹", "冲突", "战场",
        ],
    },
    # ── 备选话题 ──
    {
        "topic_name": "反腐案件通报与官员审查调查追踪",
        "category": "时政",
        "heat_score": 84,
        "summary": "追踪近期多名官员被审查调查、提起公诉的反腐案件进展，涵盖税务系统、石油系统、地方政协等。",
        "min_score": 1,
        "keywords": [
            "审查调查", "受贿", "提起公诉",
            "接受审查", "开除党籍",
            "税务局", "中石化",
            "反腐", "违纪", "落马", "被查",
            "纪委监委", "严重违纪",
        ],
        "exclude_keywords": [],
    },
    {
        "topic_name": "人民币汇率波动与央行货币政策",
        "category": "财经",
        "heat_score": 78,
        "summary": "关注人民币兑美元中间价波动、央行公开市场逆回购操作、A股走势及日元汇率暴跌的联动影响。",
        "min_score": 1,
        "keywords": [
            "人民币", "汇率", "中间价",
            "央行", "逆回购", "公开市场操作",
            "货币政策", "外汇", "日元对美元",
            "基点", "利率",
        ],
        "exclude_keywords": [],
    },
    {
        "topic_name": "中国女排新周期首秀与世联赛征程",
        "category": "体育",
        "heat_score": 78,
        "summary": "追踪中国女排在新奥运周期中的首秀表现，包括世联赛开门红、新老队员磨合与战术调整。",
        "min_score": 1,
        "keywords": [
            "中国女排", "女排", "世联赛",
            "新周期", "开门红",
            "排球", "女排精神",
        ],
        "exclude_keywords": [
            "侨界", "抗战", "台湾光复", "座谈会",
        ],
    },
    {
        "topic_name": "中国网球新星国际赛事表现追踪",
        "category": "体育",
        "heat_score": 76,
        "summary": "追踪中国网球选手郑钦文、王欣瑜、张帅、吴易昺在温网等国际赛事中的表现与晋级动态。",
        "min_score": 1,
        "keywords": [
            "网球", "温网", "郑钦文",
            "王欣瑜", "张帅", "吴易昺",
            "大满贯", "WTA", "ATP",
            "法网", "澳网", "美网",
        ],
        "exclude_keywords": [
            "WTT", "王楚钦", "孙颖莎", "王曼昱",
        ],
    },
    {
        "topic_name": "新能源汽车产业与汽车后市场发展",
        "category": "财经",
        "heat_score": 74,
        "summary": "围绕新能源汽车消费趋势、汽车后市场激活万亿蓝海、智能驾驶与充电桩产业发展等报道。",
        "min_score": 1,
        "keywords": [
            # 精确汽车词
            "新能源汽车",
            "新能源车",
            "汽车后市场",
            "智能驾驶",
            "充电桩",
            "车联网",
            "智能网联汽车",
            "汽车产业",
            "二手车",
            "汽车消费",
            "车企",
            "电动车",
            "从代步到玩车",
        ],
        "exclude_keywords": [
            "网络安全宣传周", "网安周",
            "网络诈骗", "网络谣言",
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════
# 数据库连接
# ═══════════════════════════════════════════════════════════════════════

def get_connection():
    """创建 MySQL 数据库连接。"""
    try:
        import pymysql
    except ImportError:
        print("ERROR: pymysql 未安装。请执行: pip install pymysql")
        sys.exit(1)

    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.Error as exc:
        print(f"ERROR: 数据库连接失败 — {exc}")
        print(f"  Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"  Database: {DB_CONFIG['database']}")
        print(f"  User: {DB_CONFIG['user']}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════
# 数据加载
# ═══════════════════════════════════════════════════════════════════════

def load_unassigned_news(conn) -> list[dict[str, Any]]:
    """读取所有未分配 topic_id 的有效新闻。"""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            n.id,
            n.title,
            n.source,
            n.publish_time,
            COALESCE(c.name, '') AS category_name
        FROM news n
        LEFT JOIN news_category c ON n.category_id = c.id
        WHERE n.topic_id IS NULL
          AND n.status = 1
        ORDER BY n.publish_time DESC
        """
    )
    rows = cursor.fetchall()
    return [
        {
            "id": r[0],
            "title": r[1] or "",
            "source": r[2] or "",
            "publish_time": str(r[3]) if r[3] else "",
            "category_name": r[4] or "",
        }
        for r in rows
    ]


# ═══════════════════════════════════════════════════════════════════════
# 匹配逻辑
# ═══════════════════════════════════════════════════════════════════════

def is_valid_keyword(kw: str) -> bool:
    """排除单字关键词（避免误匹配过多）。"""
    return len(kw.strip()) >= 2


def match_topic_for_news(
    news_title: str,
    topics: list[dict[str, Any]],
) -> tuple[int | None, list[str], list[dict[str, Any]]]:
    """对单条新闻标题执行关键词匹配。

    Returns:
        (best_topic_index, matched_keywords, all_matches)
        - best_topic_index: 最佳匹配 topic 索引，冲突时为 None
        - matched_keywords: 最佳 topic 命中的关键词列表
        - all_matches: 所有候选匹配 [{topic_index, topic_name, score, keywords}]
    """
    title_lower = news_title.lower()
    all_matches: list[dict[str, Any]] = []

    for idx, topic in enumerate(topics):
        keywords = topic.get("keywords", [])
        exclude_keywords = topic.get("exclude_keywords", [])

        # 检查排除词
        excluded = False
        for ek in exclude_keywords:
            if is_valid_keyword(ek) and ek.lower() in title_lower:
                excluded = True
                break
        if excluded:
            continue

        # 命中关键词
        hits = []
        for kw in keywords:
            if not is_valid_keyword(kw):
                continue
            if kw.lower() in title_lower:
                hits.append(kw)

        # 检查最低匹配分
        min_score = topic.get("min_score", 1)
        if hits and len(hits) >= min_score:
            all_matches.append({
                "topic_index": idx,
                "topic_name": topic["topic_name"],
                "score": len(hits),
                "keywords": hits,
            })

    if not all_matches:
        return None, [], []

    # 按分数降序
    all_matches.sort(key=lambda m: -m["score"])

    best = all_matches[0]
    tied = [m for m in all_matches if m["score"] == best["score"]]

    if len(tied) > 1:
        # 冲突：多个 topic 同分
        return None, [], all_matches

    return best["topic_index"], best["keywords"], all_matches


# ═══════════════════════════════════════════════════════════════════════
# Dry-run 核心
# ═══════════════════════════════════════════════════════════════════════

def run_dry_run(conn, topics: list[dict[str, Any]]):
    """执行 dry-run，不写数据库。"""
    news_list = load_unassigned_news(conn)

    # 每个 topic 的匹配结果
    topic_matches: dict[int, list[dict[str, Any]]] = defaultdict(list)
    unmatched: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    total_matched = 0

    for news in news_list:
        best_idx, hit_keywords, all_matches = match_topic_for_news(
            news["title"], topics
        )

        if best_idx is None and not all_matches:
            unmatched.append(news)
            continue

        if best_idx is None:
            # 冲突
            conflicts.append({**news, "all_matches": all_matches})
            continue

        topic_matches[best_idx].append({
            **news,
            "matched_keywords": hit_keywords,
        })
        total_matched += 1

    return {
        "total_unassigned": len(news_list),
        "total_matched": total_matched,
        "total_unmatched": len(unmatched),
        "total_conflicts": len(conflicts),
        "topic_matches": dict(topic_matches),
        "unmatched": unmatched,
        "conflicts": conflicts,
    }


# ═══════════════════════════════════════════════════════════════════════
# 输出
# ═══════════════════════════════════════════════════════════════════════

def print_report(results: dict, topics: list[dict[str, Any]]):
    """格式化输出 dry-run 结果。"""
    print("=" * 70)
    print("  Timeline Topic Assignment — DRY RUN")
    print("  (NO database writes — preview only)")
    print("=" * 70)
    print()
    print(f"  Total unassigned news  : {results['total_unassigned']}")
    print(f"  Matched news           : {results['total_matched']}")
    print(f"  Unmatched news         : {results['total_unmatched']}")
    print(f"  Conflict news          : {results['total_conflicts']}")
    print()

    # ── 逐 topic 输出 ──
    for idx, topic in enumerate(topics):
        matches = results["topic_matches"].get(idx, [])
        count = len(matches)
        status = "[OK]" if count >= 2 else "❌ (< 2 news, cannot generate timeline)"

        print("-" * 70)
        print(f"  Topic {idx + 1}: {topic['topic_name']}")
        print(f"  Category: {topic.get('category', '-')}")
        print(f"  Heat Score: {topic.get('heat_score', '-')}")
        print(f"  Matched: {count}  {status}")
        print()

        # 按 publish_time 排序
        matches_sorted = sorted(
            matches,
            key=lambda m: m.get("publish_time", ""),
            reverse=True,
        )

        for m in matches_sorted:
            title = m["title"][:80]
            kw_str = ", ".join(m.get("matched_keywords", []))
            print(f"    [{m['id']}] {title}")
            print(f"         source: {m.get('source', '-')}")
            print(f"         time:   {m.get('publish_time', '-')}")
            print(f"         keywords: {kw_str}")
            print()

    # ── 冲突新闻 ──
    if results["conflicts"]:
        print("-" * 70)
        print(f"  [!]  CONFLICTS ({len(results['conflicts'])} news)")
        print("  (multiple topics tied for best match)")
        print()
        for c in results["conflicts"]:
            print(f"    [{c['id']}] {c['title'][:80]}")
            for m in c.get("all_matches", []):
                kw_str = ", ".join(m.get("keywords", []))
                print(f"         → {m['topic_name']} (score={m['score']})  [{kw_str}]")
            print()

    # ── 未匹配抽样 ──
    if results["unmatched"]:
        print("-" * 70)
        print(f"  UNMATCHED ({len(results['unmatched'])} news — showing first 30)")
        print()
        for u in results["unmatched"][:30]:
            title = u["title"][:80]
            cat = u.get("category_name", "-")
            print(f"    [{u['id']}] [{cat}] {title}")

    # ── 汇总表 ──
    print()
    print("=" * 70)
    print("  SUMMARY BY TOPIC")
    print("=" * 70)
    print(f"  {'Topic':<40} {'Matched':>8}  {'>=2?':>5}  {'Suggest'}")
    print("-" * 70)
    for idx, topic in enumerate(topics):
        count = len(results["topic_matches"].get(idx, []))
        ok = "[OK]" if count >= 2 else "❌"
        if count >= 5:
            suggest = "优先入库"
        elif count >= 2:
            suggest = "建议入库"
        elif count == 1:
            suggest = "需补充新闻"
        else:
            suggest = "不推荐"
        print(f"  {topic['topic_name']:<40} {count:>8}  {ok:>5}  {suggest}")
    print("-" * 70)
    print(f"  {'总计':<40} {results['total_matched']:>8}")
    print()


# ═══════════════════════════════════════════════════════════════════════
# Apply — 安全写库
# ═══════════════════════════════════════════════════════════════════════

def print_backup_warning():
    """打印数据备份提示。"""
    print()
    print("=" * 70)
    print("  [!] BACKUP WARNING")
    print("=" * 70)
    print()
    print("  Before applying, please backup:")
    print("    1. news_topic table")
    print("    2. news.topic_id column")
    print("    3. event_timeline table")
    print()
    print("  Suggested backup commands:")
    print(f"    mysqldump -u{DB_CONFIG['user']} -p {DB_CONFIG['database']} \\")
    print(f"      news_topic event_timeline > backup_timeline_tables.sql")
    print()
    print(f"    mysql -u{DB_CONFIG['user']} -p {DB_CONFIG['database']} \\")
    print(f"      -e \"SELECT id, topic_id FROM news\" > backup_news_topic_mapping.csv")
    print()
    print("=" * 70)
    print()


def run_dry_run_collect(
    conn, topics: list[dict[str, Any]]
) -> dict[str, Any]:
    """收集 dry-run 匹配结果，供 apply 模式使用。"""
    news_list = load_unassigned_news(conn)
    topic_matches: dict[int, list[dict[str, Any]]] = defaultdict(list)
    unmatched: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    total_matched = 0

    for news in news_list:
        best_idx, hit_keywords, all_matches = match_topic_for_news(
            news["title"], topics
        )
        if best_idx is None and not all_matches:
            unmatched.append(news)
            continue
        if best_idx is None:
            conflicts.append({**news, "all_matches": all_matches})
            continue
        topic_matches[best_idx].append({
            **news,
            "matched_keywords": hit_keywords,
        })
        total_matched += 1

    return {
        "total_unassigned": len(news_list),
        "total_matched": total_matched,
        "total_unmatched": len(unmatched),
        "total_conflicts": len(conflicts),
        "topic_matches": dict(topic_matches),
        "unmatched": unmatched,
        "conflicts": conflicts,
    }


def ensure_topic_exists(conn, cursor, topic: dict[str, Any]) -> int | None:
    """确保 topic 在 news_topic 表中存在，返回 topic_id。

    如果同名 topic_name 已存在则复用；不存在则 INSERT。
    """
    topic_name = topic["topic_name"]
    cursor.execute(
        "SELECT id FROM news_topic WHERE topic_name = %s LIMIT 1",
        (topic_name,),
    )
    existing = cursor.fetchone()
    if existing:
        return existing[0]

    keyword_list_json = json.dumps(
        topic.get("keywords", []), ensure_ascii=False
    )
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO news_topic (topic_name, keyword_list, summary, heat_score, status, created_at, updated_at)
        VALUES (%s, %s, %s, %s, 1, %s, %s)
        """,
        (
            topic_name,
            keyword_list_json,
            topic.get("summary", ""),
            topic.get("heat_score", 70),
            now,
            now,
        ),
    )
    return cursor.lastrowid


def apply_news_topics(
    conn,
    topics: list[dict[str, Any]],
    results: dict[str, Any],
    force: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    """将匹配结果写入数据库。必须在事务中运行。"""
    import pymysql

    stats = {
        "topics_new": 0,
        "topics_reused": 0,
        "news_updated": 0,
        "news_skipped_conflict": results.get("total_conflicts", 0),
        "news_skipped_unmatched": results.get("total_unmatched", 0),
        "news_skipped_has_topic": 0,
        "news_limited": 0,
        "per_topic": {},
        "committed": False,
        "errors": [],
    }

    cursor = conn.cursor()

    try:
        # ── Step 1: 写入/复用 topic ──
        topic_id_map: dict[int, int] = {}  # candidate_index → real_topic_id
        for idx, topic in enumerate(topics):
            exists = cursor.execute(
                "SELECT id FROM news_topic WHERE topic_name = %s LIMIT 1",
                (topic["topic_name"],),
            )
            existing_row = cursor.fetchone()
            if existing_row:
                tid = existing_row[0]
                topic_id_map[idx] = tid
                stats["topics_reused"] += 1
                print(f"  [reuse] Topic '{topic['topic_name']}' → id={tid}")
            else:
                import json as _json
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    """
                    INSERT INTO news_topic (topic_name, keyword_list, summary, heat_score, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, 1, %s, %s)
                    """,
                    (
                        topic["topic_name"],
                        _json.dumps(topic.get("keywords", []), ensure_ascii=False),
                        topic.get("summary", ""),
                        topic.get("heat_score", 70),
                        now,
                        now,
                    ),
                )
                tid = cursor.lastrowid
                topic_id_map[idx] = tid
                stats["topics_new"] += 1
                print(f"  [new]   Topic '{topic['topic_name']}' → id={tid}")

        # ── Step 2: 更新 news.topic_id ──
        applied = 0
        topic_counts: dict[int, int] = defaultdict(int)

        for idx, topic in enumerate(topics):
            tid = topic_id_map.get(idx)
            if not tid:
                continue
            matches = results["topic_matches"].get(idx, [])
            for m in matches:
                if limit is not None and applied >= limit:
                    stats["news_limited"] = len(matches) - applied  # approximate
                    break

                news_id = m["id"]
                if not force:
                    cursor.execute(
                        "SELECT topic_id FROM news WHERE id = %s",
                        (news_id,),
                    )
                    row = cursor.fetchone()
                    if row and row[0] is not None:
                        stats["news_skipped_has_topic"] += 1
                        continue

                cursor.execute(
                    "UPDATE news SET topic_id = %s WHERE id = %s",
                    (tid, news_id),
                )
                applied += 1
                topic_counts[idx] += 1

        stats["news_updated"] = applied
        stats["per_topic"] = {
            topics[idx]["topic_name"]: topic_counts.get(idx, 0)
            for idx in range(len(topics))
        }

        # ── Step 3: commit ──
        conn.commit()
        stats["committed"] = True
    except Exception as exc:
        conn.rollback()
        stats["errors"].append(str(exc))

    return stats


def print_apply_stats(stats: dict):
    """输出 apply 执行统计。"""
    print()
    print("=" * 70)
    if stats["committed"]:
        print("  APPLY COMPLETE — committed")
    else:
        print("  APPLY FAILED — rolled back")
    print("=" * 70)
    print()
    print(f"  Topics new    : {stats['topics_new']}")
    print(f"  Topics reused : {stats['topics_reused']}")
    print(f"  News updated  : {stats['news_updated']}")
    print(f"  Skipped (conflict)   : {stats['news_skipped_conflict']}")
    print(f"  Skipped (unmatched)  : {stats['news_skipped_unmatched']}")
    print(f"  Skipped (has topic)  : {stats['news_skipped_has_topic']}")
    if stats["errors"]:
        print(f"  Errors: {', '.join(stats['errors'])}")
    print()
    if stats["per_topic"]:
        print("  Per-topic breakdown:")
        for name, count in stats["per_topic"].items():
            print(f"    {name}: {count}")
    print()


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def _safe_print(*args, **kwargs):
    """Windows 兼容的安全打印，避免 GBK emoji 编码错误。"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 回退：将非 ASCII 字符替换为 ?
        safe_args = []
        for a in args:
            if isinstance(a, str):
                safe_args.append(a.encode("ascii", errors="replace").decode("ascii"))
            else:
                safe_args.append(a)
        print(*safe_args, **kwargs)


def main():
    # 在 Windows 上强制 stdout 使用 utf-8
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="Timeline 事件脉络 — 候选话题归类脚本"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="预览匹配结果（不写数据库）",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="写入数据库（必须同时使用 --confirm）",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        default=False,
        help="确认执行写库操作（仅与 --apply 同时生效）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="允许覆盖已有 topic_id（默认只处理 topic_id IS NULL）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制最大更新新闻数（用于小批量测试）",
    )
    args = parser.parse_args()

    # ── 默认 dry-run ──
    if not args.apply and not args.dry_run:
        args.dry_run = True

    # ── apply 模式：安全保护 ──
    if args.apply:
        # 始终先打印备份提醒
        print_backup_warning()

        if not args.confirm:
            print("=" * 70)
            print("  --apply requires --confirm.")
            print("  Please backup your database and review --dry-run")
            print("  results before applying.")
            print()
            print("  Once ready, run:")
            print("    python scripts/assign_news_topics.py --apply --confirm")
            print("=" * 70)
            return

        # --apply --confirm：真正写库
        print(f"\n  Connecting to {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']} ...")
        conn = get_connection()
        print("  Connected. Running dry-run collection + apply...\n")

        try:
            results = run_dry_run_collect(conn, TOPIC_CANDIDATES)
            print(f"  Dry-run done: {results['total_matched']} matched, "
                  f"{results['total_unmatched']} unmatched, "
                  f"{results['total_conflicts']} conflicts.\n")

            # 二次确认
            print("-" * 70)
            response = input(
                "  [!!] This WILL write to the database. "
                "Type 'YES' to confirm: "
            ).strip()
            if response != "YES":
                print("  Aborted by user. No writes performed.")
                return

            stats = apply_news_topics(
                conn, TOPIC_CANDIDATES, results,
                force=args.force,
                limit=args.limit,
            )
            print_apply_stats(stats)
        finally:
            conn.close()
        return

    # ── dry-run 模式 ──
    print(f"\n  Connecting to {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']} ...")
    conn = get_connection()
    print("  Connected. Running dry-run...\n")

    try:
        results = run_dry_run(conn, TOPIC_CANDIDATES)
        print_report(results, TOPIC_CANDIDATES)
    finally:
        conn.close()

    print("  Dry-run complete. No database writes were performed.\n")


if __name__ == "__main__":
    main()
