#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""M12 Analytics Demo Data Seeder

向开发数据库中插入 M12_DEMO 标记的演示数据，用于验证数据看板页面。
仅用于开发环境，不应用于生产数据库。

Usage:
  cd backend
  .venv\Scripts\python.exe ../scripts/seed_m12_analytics_demo.py

Safety:
  - 所有演示数据均标注 M12_DEMO（标题/描述/备注）。
  - 使用 INSERT IGNORE 或幂等检查避免重复插入。
  - 不修改/删除 admin/editor/user 三个基础账号。
  - 不删除任何已有真实数据。
"""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pymysql

# ── Database connection ─────────────────────────────────────────────
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "llm_news_user",
    "password": "123456",
    "database": "llm_news_system",
    "charset": "utf8mb4",
}

# Demo marker — all demo content carries this string
DEMO = "M12_DEMO"

# Existing real reference IDs
EXISTING_NEWS = list(range(1, 427))  # 426 real news
EXISTING_POSTS = [1, 2, 3, 4, 5, 6]
EXISTING_TOPICS = [1, 2, 3]
EXISTING_CATEGORIES = [1, 2, 3, 4, 5, 6, 7]
EXISTING_USERS = [1, 2, 3, 4]
EXISTING_NEWS_COMMENT_IDS = list(range(1, 4))  # max 3
EXISTING_POST_COMMENT_IDS = list(range(1, 20))  # max 19

# ── Helpers ─────────────────────────────────────────────────────────

def _d(days_ago: int = 0, hour: int = 0, minute: int = 0) -> str:
    """Return a datetime string `days_ago` days back from now."""
    ts = datetime.now() - timedelta(days=days_ago, hours=-hour, minutes=-minute)
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def _rand_date(days_range: int = 90) -> str:
    days = random.randint(1, days_range)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    return _d(days, hour, minute)


def _tags(tag_list: list[str]) -> str:
    return json.dumps(tag_list, ensure_ascii=False)


def _json(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False)


def conn() -> pymysql.connections.Connection:
    return pymysql.connect(**DB_CONFIG)


def _exists(c: pymysql.connections.Connection, table: str, where: str, params: list) -> bool:
    c.execute(f"SELECT 1 FROM {table} WHERE {where} LIMIT 1", params)
    return c.fetchone() is not None


# ── 1. News (30-60, target ~45) ─────────────────────────────────────

NEWS_TEMPLATES = [
    ("M12_DEMO 人工智能应用新闻：{topic}", "人工智能技术正在{domain}加速落地。", 5),
    ("M12_DEMO 城市治理新闻：{topic}", "城市治理数字化转型取得新进展，{topic}成为焦点。", 3),
    ("M12_DEMO 教育科技新闻：{topic}", "教育科技赋能{domain}，教学方式发生深刻变化。", 2),
    ("M12_DEMO 医疗健康新闻：{topic}", "医疗健康领域引入新技术，{topic}改善患者体验。", 4),
    ("M12_DEMO 低空经济新闻：{topic}", "低空经济持续发展，{topic}开辟新应用场景。", 2),
    ("M12_DEMO 国际科技新闻：{topic}", "国际科技合作深化，{topic}引起广泛关注。", 8),
    ("M12_DEMO 财经数据新闻：{topic}", "财经数据发布，{topic}影响市场预期。", 4),
    ("M12_DEMO 娱乐产业新闻：{topic}", "娱乐产业融合发展，{topic}创新内容形态。", 7),
    ("M12_DEMO 体育时事新闻：{topic}", "体育赛事精彩纷呈，{topic}刷新纪录。", 6),
    ("M12_DEMO 文化传播新闻：{topic}", "文化传播新趋势，{topic}促进中外交流。", 1),
]

TOPIC_WORDS = [
    "智能摘要技术成熟度评估", "大模型应用落地", "数据安全与隐私保护",
    "边缘计算新突破", "区块链在新闻中的应用", "5G+AI融合场景",
    "智慧城市标杆项目", "社区治理数字化", "数字孪生城市",
    "在线教育个性化", "虚拟教研室建设", "AI辅助教学工具",
    "远程医疗服务", "智能诊断系统", "基因测序进展",
    "无人机物流常态化", "空域管理改革", "低空经济示范区",
    "国际AI治理对话", "跨境数据流动规则", "全球数字合作",
]


def _fill_template(template: str, topic_word: str) -> str:
    """Fill both {topic} and {domain} placeholders with the same word."""
    return template.replace("{topic}", topic_word).replace("{domain}", topic_word)


def seed_news(c: pymysql.connections.Connection) -> int:
    count = 0
    skip_count = 0
    for i in range(50):
        tmpl = random.choice(NEWS_TEMPLATES)
        topic_word = random.choice(TOPIC_WORDS)
        title = _fill_template(tmpl[0], topic_word)
        summary = _fill_template(tmpl[1], topic_word) + " " + DEMO
        content = (
            "<p>" + DEMO + " 演示新闻正文。关于 " + topic_word + " 的详细报道。</p>"
            "<p>该领域在近期的技术突破和政策支持下快速发展。"
            "业内专家认为，" + topic_word + " 将在未来几年内持续释放产业价值。</p>"
            "<p>本次报道综合多方信息来源，为读者提供全面、客观的行业观察视角。</p>"
        )
        category_id = tmpl[2]
        topic_id = random.choice(EXISTING_TOPICS) if random.random() > 0.3 else None
        publish_time = _rand_date(90)
        status = random.choices([1, 1, 1, 1, 0, 3], weights=[40, 40, 15, 11, 4, 5])[0]
        source_url = f"https://demo.example.com/m12_news_{i}"
        tags = _tags([DEMO, random.choice(["科技", "社会", "财经", "教育", "医疗", "产业"])])

        if _exists(c, "news", "source_url = %s", [source_url]):
            skip_count += 1
            continue

        view_count = random.randint(5, 500)
        like_count = random.randint(0, view_count // 3)
        comment_count = random.randint(0, like_count)
        favorite_count = random.randint(0, like_count // 2)

        c.execute(
            """INSERT INTO news
               (title, summary, content, category_id, topic_id, source, editor,
                publish_time, source_url, view_count, like_count, comment_count,
                favorite_count, tags, status, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            [
                title, summary, content, category_id, topic_id, f"{DEMO}数据源", f"{DEMO}编辑",
                publish_time, source_url, view_count, like_count, comment_count,
                favorite_count, tags, status, publish_time, publish_time,
            ],
        )
        count += 1

    print("  news: inserted " + str(count) + ", skipped " + str(skip_count) + " (duplicate source_url)")
    return count


# ── 2. Community Posts (15-30, target ~25) ──────────────────────────

POST_TEMPLATES = [
    ("M12_DEMO 热点讨论：{topic}", "关于{topic}，大家怎么看？欢迎讨论。"),
    ("M12_DEMO 新闻观点：{topic}", "读了{topic}相关新闻，分享几点看法。"),
    ("M12_DEMO AI 摘要体验反馈：{topic}", "试用 AI 摘要功能后，对{topic}类新闻的摘要效果评价。"),
    ("M12_DEMO 事件脉络讨论：{topic}", "{topic}的事件脉络整理得怎么样？有没有遗漏的关键节点？"),
    ("M12_DEMO 社区互动：{topic}", "看到社区关于{topic}的讨论很活跃，补充一些背景信息。"),
]


def seed_posts(c: pymysql.connections.Connection) -> int:
    count = 0
    for i in range(25):
        tmpl = random.choice(POST_TEMPLATES)
        topic_word = random.choice(TOPIC_WORDS[:15])
        title = tmpl[0].format(topic=topic_word)
        content = (
            f"{DEMO} {tmpl[1].format(topic=topic_word)}\n\n"
            f"补充观点：{topic_word} 在近期报道中多次出现，从不同角度观察，"
            f"可以发现一些值得深入讨论的趋势。欢迎大家补充更多信息。"
        )
        user_id = random.choice(EXISTING_USERS)
        related_news_id = random.choice(EXISTING_NEWS) if random.random() > 0.3 else None
        topic_id = random.choice(EXISTING_TOPICS) if random.random() > 0.5 else None
        create_time = _rand_date(90)
        status = random.choices([1, 1, 1, 3, 2, 4], weights=[50, 35, 10, 8, 5, 2])[0]
        like_count = random.randint(0, 80)
        comment_count = random.randint(0, like_count // 2)
        favorite_count = random.randint(0, like_count // 3)
        heat_score = like_count * 3 + comment_count * 5 + favorite_count * 4 + random.randint(0, 50)
        tags = _tags([DEMO, random.choice(["讨论", "观点", "反馈", "脉络", "互动"])])

        c.execute(
            """INSERT INTO community_post
               (user_id, title, content, related_news_id, topic_id, tags,
                like_count, comment_count, favorite_count, heat_score, status,
                created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            [
                user_id, title, content, related_news_id, topic_id, tags,
                like_count, comment_count, favorite_count, heat_score, status,
                create_time, create_time,
            ],
        )
        count += 1

    print(f"  community_post: inserted {count}")
    return count


# ── 3. News Comments (30-80, target ~50) ────────────────────────────

NEWS_COMMENT_CONTENTS = [
    "M12_DEMO 这条新闻很有参考价值，数据翔实。",
    "M12_DEMO 希望看到事件后续进展，持续关注。",
    "M12_DEMO 摘要结果比较清晰，对理解新闻有帮助。",
    "M12_DEMO 这个观点需要进一步核实，建议补充来源。",
    "M12_DEMO 报道角度很全面，赞一个。",
    "M12_DEMO 对普通读者来说信息量有点大，希望有更简洁的版本。",
    "M12_DEMO 和之前一条相关报道放在一起看更有收获。",
    "M12_DEMO 细节很到位，但整体逻辑可以更清晰一些。",
    "M12_DEMO 技术进步确实带来了很多变化，但也要关注潜在风险。",
    "M12_DEMO 政策层面的分析还比较到位，期待后续政策细则。",
]


def seed_news_comments(c: pymysql.connections.Connection) -> int:
    count = 0
    for i in range(50):
        news_id = random.choice(EXISTING_NEWS)
        user_id = random.choice(EXISTING_USERS)
        content = random.choice(NEWS_COMMENT_CONTENTS)
        create_time = _rand_date(90)
        status = random.choices([1, 1, 1, 1, 3, 2, 4], weights=[60, 30, 15, 10, 8, 5, 2])[0]
        like_count = random.randint(0, 25)
        parent_id = (
            random.choice(EXISTING_NEWS_COMMENT_IDS) if random.random() > 0.85 else None
        )

        c.execute(
            """INSERT INTO news_comment
               (news_id, user_id, parent_id, content, like_count, status, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            [news_id, user_id, parent_id, content, like_count, status, create_time, create_time],
        )
        count += 1

    print(f"  news_comment: inserted {count}")
    return count


# ── 4. Post Comments (30-80, target ~50) ────────────────────────────

POST_COMMENT_CONTENTS = [
    "M12_DEMO 这个讨论很有意义，补充一些信息。",
    "M12_DEMO 同意楼主的观点，社区需要更多这类讨论。",
    "M12_DEMO 有不同的看法，容我展开说一下。",
    "M12_DEMO 之前也注意到这个问题，终于有人讨论了。",
    "M12_DEMO 建议开设专门的版块深入讨论这个话题。",
    "M12_DEMO 从另一个角度分析，可能结论会不一样。",
    "M12_DEMO 这些数据从哪里来的？想看看原始出处。",
    "M12_DEMO 思路很好，但实施起来可能面临一些挑战。",
    "M12_DEMO 感谢分享，收藏了这条讨论。",
    "M12_DEMO 和新闻原文对照着看更有价值。",
]


def seed_post_comments(c: pymysql.connections.Connection) -> int:
    count = 0
    # Also comment on M12_DEMO posts (we'll query them)
    c.execute("SELECT id FROM community_post WHERE title LIKE %s", [f"%{DEMO}%"])
    demo_post_ids = [r[0] for r in c.fetchall()]
    all_post_ids = EXISTING_POSTS + demo_post_ids

    for i in range(50):
        post_id = random.choice(all_post_ids)
        user_id = random.choice(EXISTING_USERS)
        content = random.choice(POST_COMMENT_CONTENTS)
        create_time = _rand_date(90)
        status = random.choices([1, 1, 1, 1, 3, 2, 4], weights=[60, 30, 15, 10, 8, 5, 2])[0]
        like_count = random.randint(0, 20)
        parent_id = (
            random.choice(EXISTING_POST_COMMENT_IDS) if random.random() > 0.85 else None
        )

        c.execute(
            """INSERT INTO post_comment
               (post_id, user_id, parent_id, content, like_count, status, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            [post_id, user_id, parent_id, content, like_count, status, create_time, create_time],
        )
        count += 1

    print(f"  post_comment: inserted {count}")
    return count


# ── 5. AI Generate Records (30-80, target ~50) ──────────────────────

def seed_ai_records(c: pymysql.connections.Connection) -> int:
    count = 0
    function_types = ["title_summary", "consistency_check", "keyword_extract", "timeline_generate"]
    risk_levels = ["low", "medium", "high"]
    statuses = ["success", "failed", "fallback"]
    # status weights: mostly success, some fallback, some failed
    status_weights = [60, 15, 25]

    for i in range(50):
        user_id = random.choice(EXISTING_USERS)
        function_type = random.choice(function_types)
        source_news_id = random.choice(EXISTING_NEWS) if random.random() > 0.2 else None
        source_title = f"{DEMO} AI生成测试新闻 #{i}" if not source_news_id else None
        create_time = _rand_date(90)
        status = random.choices(statuses, weights=status_weights)[0]

        # Risk level depends on function type
        if function_type == "consistency_check":
            risk_level = random.choices(risk_levels + ["unknown"], weights=[30, 30, 20, 20])[0]
        elif function_type == "timeline_generate":
            risk_level = random.choices(risk_levels + ["unknown"], weights=[35, 25, 15, 25])[0]
        else:
            risk_level = random.choices(risk_levels + ["unknown"], weights=[50, 20, 5, 25])[0]

        check_result = _json({
            "consistency": {
                "score": random.randint(40, 98),
                "risk_level": risk_level,
                "issues": [] if risk_level == "low" else ["M12_DEMO sample issue"],
                "suggestions": [],
            },
            "source": DEMO,
        })

        candidate_titles = _json([
            f"{DEMO} 候选标题 A-{i}",
            f"{DEMO} 候选标题 B-{i}",
            f"{DEMO} 候选标题 C-{i}",
        ])

        keywords = _json([DEMO, random.choice(["科技", "治理", "教育", "医疗", "经济", "文化"])])
        input_text = f"{DEMO} 输入文本 #{i}：用于测试 AI 生成效果的演示内容。"
        summary_short = f"{DEMO} 短摘要 #{i}" if random.random() > 0.1 else None
        summary_long = f"{DEMO} 长摘要 #{i}：详细版本的摘要内容，包含更多背景和细节信息。" if random.random() > 0.2 else None

        c.execute(
            """INSERT INTO ai_generate_record
               (user_id, source, source_news_id, source_title, input_text,
                title_count, summary_type, candidate_titles, summary_short, summary_long,
                keywords, risk_level, check_result, status, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            [
                user_id, DEMO if not source_news_id else "manual", source_news_id,
                source_title or f"{DEMO} 源标题 #{i}",
                input_text, 3, "generate", candidate_titles, summary_short, summary_long,
                keywords, risk_level, check_result,
                1 if status == "success" else (2 if status == "fallback" else 0),
                create_time, create_time,
            ],
        )
        count += 1

    print(f"  ai_generate_record: inserted {count}")
    return count


# ── 6. Browse History (100-300, target ~200) ────────────────────────

def seed_browse_history(c: pymysql.connections.Connection) -> int:
    count = 0
    for i in range(200):
        user_id = random.choice(EXISTING_USERS)
        news_id = random.choice(EXISTING_NEWS)
        browse_time = _rand_date(90)
        target_type = random.choices(["news", "post"], weights=[80, 20])[0]
        target_id = news_id if target_type == "news" else random.choice(EXISTING_POSTS)

        c.execute(
            """INSERT INTO browse_history
               (user_id, news_id, target_type, target_id, browse_time, created_at)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            [user_id, news_id, target_type, target_id, browse_time, browse_time],
        )
        count += 1

    print(f"  browse_history: inserted {count}")
    return count


# ── 7. Favorites (20-60, target ~40) ────────────────────────────────

def seed_favorites(c: pymysql.connections.Connection) -> int:
    count = 0
    # Load existing favorites into seen set to avoid duplicate key errors
    c.execute("SELECT user_id, target_type, target_id FROM favorite")
    seen = {(r[0], r[1], r[2]) for r in c.fetchall()}
    attempts = 0
    max_attempts = 100
    for i in range(max_attempts):
        if count >= 40:
            break
        attempts = i + 1
        user_id = random.choice(EXISTING_USERS)
        target_type = random.choices(["news", "post"], weights=[70, 30])[0]
        target_id = (
            random.choice(EXISTING_NEWS) if target_type == "news"
            else random.choice(EXISTING_POSTS)
        )
        key = (user_id, target_type, target_id)
        if key in seen:
            continue
        seen.add(key)
        create_time = _rand_date(90)

        c.execute(
            """INSERT INTO favorite (user_id, target_type, target_id, created_at)
               VALUES (%s,%s,%s,%s)""",
            [user_id, target_type, target_id, create_time],
        )
        count += 1

    print("  favorite: inserted " + str(count) + " (dedup from " + str(attempts) + " attempts)")
    return count


# ── 8. Admin Operation Logs (20-50, target ~35) ─────────────────────

MODULES = ["news", "post", "comment", "topic", "timeline", "user", "ai_config", "system_config", "ops"]
ACTIONS = ["view", "approve", "reject", "fold", "restore", "update", "generate", "refresh", "backup"]
RESULTS = ["success", "failed", "unsupported"]

OPERATORS = [
    (3, "admin", "admin"),
    (2, "editor", "editor"),
]

def seed_operation_logs(c: pymysql.connections.Connection) -> int:
    count = 0
    for i in range(35):
        op = random.choice(OPERATORS)
        module = random.choice(MODULES)
        action = random.choice(ACTIONS)
        result = random.choices(RESULTS, weights=[70, 15, 15])[0]
        create_time = _rand_date(90)
        target_type = module if module in ("news", "post", "comment", "topic") else "record"
        target_id = str(random.randint(1, 999))
        description = f"{DEMO} 操作记录 #{i}: {module}.{action} -> {result}"

        c.execute(
            """INSERT INTO admin_operation_log
               (operator_id, operator_name, operator_role, module, action,
                target_type, target_id, description, ip_address, user_agent,
                result, error_message, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            [
                op[0], op[1], op[2], module, action,
                target_type, target_id, description,
                "127.0.0.1", f"M12_Seed_Script/{DEMO}",
                result,
                f"{DEMO} 错误信息" if result == "failed" else "",
                create_time,
            ],
        )
        count += 1

    print(f"  admin_operation_log: inserted {count}")
    return count


# ── 9. Timeline Records (5-10) ──────────────────────────────────────

def seed_timelines(c: pymysql.connections.Connection) -> int:
    count = 0
    for topic_id in EXISTING_TOPICS:
        # Each topic gets 1-2 extra timeline entries
        for j in range(random.randint(1, 2)):
            source_ids = random.sample(EXISTING_NEWS, min(5, len(EXISTING_NEWS)))
            gen_time = _rand_date(90)
            generate_status = random.choices(
                ["generated", "generated", "generated", "failed", "not_generated"],
                weights=[50, 30, 10, 5, 5],
            )[0]

            timeline_json = _json([
                {
                    "time": (_d(random.randint(5, 90)))[:10],
                    "title": f"{DEMO} 事件节点 {k+1}",
                    "summary": f"{DEMO} 该节点概述了相关事件的关键进展。",
                    "source_news_id": sid,
                }
                for k, sid in enumerate(source_ids[:3])
            ])

            c.execute(
                """INSERT INTO event_timeline
                   (topic_id, timeline_json, source_news_ids, generate_status,
                    error_message, generated_at, created_at, updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                [
                    topic_id, timeline_json, _json(source_ids), generate_status,
                    f"{DEMO} 生成失败示例" if generate_status == "failed" else None,
                    gen_time if generate_status != "not_generated" else None,
                    gen_time, gen_time,
                ],
            )
            count += 1

    print(f"  event_timeline: inserted {count}")
    return count


# ── Main ────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("M12 Analytics Demo Data Seeder")
    print(f"Demo marker: {DEMO}")
    print("=" * 60)

    db = conn()
    try:
        with db.cursor() as c:
            # 1
            n1 = seed_news(c)
            db.commit()

            # 2
            n2 = seed_posts(c)
            db.commit()

            # 3
            n3 = seed_news_comments(c)
            db.commit()

            # 4
            n4 = seed_post_comments(c)
            db.commit()

            # 5
            n5 = seed_ai_records(c)
            db.commit()

            # 6
            n6 = seed_browse_history(c)
            db.commit()

            # 7
            n7 = seed_favorites(c)
            db.commit()

            # 8
            n8 = seed_operation_logs(c)
            db.commit()

            # 9
            n9 = seed_timelines(c)
            db.commit()

        total = n1 + n2 + n3 + n4 + n5 + n6 + n7 + n8 + n9
        print("─" * 60)
        print(f"TOTAL inserted: {total} rows across 9 tables")
        print(f"All rows marked with: {DEMO}")
        print("=" * 60)

    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
