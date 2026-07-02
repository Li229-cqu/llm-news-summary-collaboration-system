#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
后台待审核中心演示数据种子脚本

向开发数据库插入一批标记 [演示待审] 的待审核数据（status=3），
用于测试后台审核流程：审核通过、驳回、折叠、删除、恢复等操作。

适用环境：仅开发/演示环境，不应用于生产数据库。

Usage:
  cd backend
  .venv\Scripts\python.exe ../scripts/seed_admin_pending_review_demo.py

Safety:
  - 所有数据标记 [演示待审]（title/username/内容前缀），方便识别和清理。
  - 使用幂等检查避免重复插入。
  - 不修改/删除已有真实数据。
  - 不删除非本脚本插入的数据。

清理:
  python -c "from scripts.seed_admin_pending_review_demo import cleanup; cleanup()"
"""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta

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

# Demo markers — all seed data carries these strings for idempotent insert and cleanup
TITLE_PREFIX = "[演示待审]"
USER_PREFIX = "demo_review_"
CONTENT_MARKER = "【演示待审数据】"

# ── Helpers ─────────────────────────────────────────────────────────


def _d(days_ago: int = 0, hour: int = 0, minute: int = 0) -> str:
    ts = datetime.now() - timedelta(days=days_ago, hours=-hour, minutes=-minute)
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def _rand_date(days_range: int = 7) -> str:
    days = random.randint(1, days_range)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    return _d(days, hour, minute)


def _tags(tag_list: list[str]) -> str:
    return json.dumps(tag_list, ensure_ascii=False)


def get_conn() -> pymysql.connections.Connection:
    return pymysql.connect(**DB_CONFIG)


def _exists(c, table: str, where: str, params: list) -> bool:
    c.execute(f"SELECT 1 FROM {table} WHERE {where} LIMIT 1", params)
    return c.fetchone() is not None


def _fetch_ids(c, table: str, column: str = "id", where: str = "1=1", params: list | None = None) -> list[int]:
    c.execute(f"SELECT {column} FROM {table} WHERE {where}", params or [])
    return [r[0] for r in c.fetchall()]


# ═════════════════════════════════════════════════════════════════════
# 1. 测试用户 (7个)
# ═════════════════════════════════════════════════════════════════════

DEMO_USERS = [
    ("demo_review_user_01", "123456", "演示小明", "user"),
    ("demo_review_user_02", "123456", "演示小红", "user"),
    ("demo_review_user_03", "123456", "演示小刚", "user"),
    ("demo_review_user_04", "123456", "演示小丽", "user"),
    ("demo_review_user_05", "123456", "演示大飞", "user"),
    ("demo_review_user_06", "123456", "演示阿花", "user"),
    ("demo_review_user_07", "123456", "演示老王", "user"),
]


def seed_test_users(c) -> list[int]:
    """Insert demo users if not exist, return their IDs."""
    ids = []
    for username, password, nickname, role in DEMO_USERS:
        if _exists(c, "user", "username = %s", [username]):
            c.execute("SELECT id FROM user WHERE username = %s", [username])
            ids.append(c.fetchone()[0])
            continue
        c.execute(
            """INSERT INTO user (username, password, nickname, role, avatar, status, created_at, updated_at)
               VALUES (%s, %s, %s, %s, '', 1, NOW(), NOW())""",
            [username, password, nickname, role],
        )
        ids.append(c.lastrowid)
    print(f"  user: {len(ids)} demo users ready (IDs: {ids})")
    return ids


# ═════════════════════════════════════════════════════════════════════
# 2. 测试话题 (补充 5 个)
# ═════════════════════════════════════════════════════════════════════

DEMO_TOPICS = [
    ("高校毕业生就业形势", "高校毕业生就业相关政策与趋势分析",
     json.dumps(["就业", "高校毕业生", "招聘", "职场"]), 65),
    ("极端天气与防灾减灾", "极端天气频发，防灾减灾和气候适应成为社会关注焦点",
     json.dumps(["极端天气", "防灾", "气候", "暴雨"]), 75),
    ("体育赛事与体育产业", "国内外体育赛事及体育产业发展动态",
     json.dumps(["体育", "赛事", "奥运", "足球"]), 60),
    ("文旅消费与假日经济", "文化旅游消费趋势与假日经济数据",
     json.dumps(["文旅", "消费", "旅游", "假日经济"]), 55),
    ("AI生成内容与谣言识别", "AI生成内容的真实性、谣言识别与信息核实",
     json.dumps(["AI生成", "谣言", "真实性", "辟谣"]), 70),
]


def seed_topics(c) -> list[int]:
    """Insert additional demo topics if not exist, return all active topic IDs."""
    for topic_name, summary, keyword_list, heat_score in DEMO_TOPICS:
        if not _exists(c, "news_topic", "topic_name = %s", [topic_name]):
            c.execute(
                """INSERT INTO news_topic (topic_name, summary, keyword_list, heat_score, status, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, 1, NOW(), NOW())""",
                [topic_name, summary, keyword_list, heat_score],
            )
    all_ids = _fetch_ids(c, "news_topic", "id", "status = 1")
    print(f"  news_topic: {len(all_ids)} topics available (IDs: {all_ids})")
    return all_ids


# ═════════════════════════════════════════════════════════════════════
# 3. 待审核新闻 (12条)
# ═════════════════════════════════════════════════════════════════════

PENDING_NEWS = [
    # ── 正常新闻稿件，适合通过审核 ──
    {
        "title": f"{TITLE_PREFIX} 大模型应用加速落地：多家企业推出行业专用AI助手",
        "summary": "随着大模型技术日趋成熟，多家科技企业近期面向金融、医疗、法律等行业推出专用AI助手产品，推动AI从通用能力向行业深度应用转型。",
        "content": (
            "<p>2026年上半年，国内大模型产业进入行业应用深化阶段。包括百度、阿里巴巴、腾讯在内的多家科技企业，相继发布了面向金融、医疗、法律、教育等垂直领域的专用AI助手产品。</p>"
            "<p>在金融领域，AI助手可辅助完成研报摘要、风险提示和市场数据分析；在医疗领域，AI辅助诊断系统已经在多家三甲医院试点应用；在法律领域，AI文书生成和案例检索工具显著提高了律师工作效率。</p>"
            "<p>业内专家认为，行业专用AI助手的普及将大幅降低企业智能化转型门槛，但同时也需要关注数据安全、隐私保护和算法公平性等问题。</p>"
        ),
        "category_id": 5, "topic": "人工智能技术发展",
        "source": "科技日报", "editor": "演示编辑",
        "tags": _tags(["大模型", "AI助手", "行业应用", "演示待审"]),
    },
    # ── 标题党新闻 ──
    {
        "title": f"{TITLE_PREFIX} 震惊！AI即将取代所有编辑，新闻行业面临末日危机？！",
        "summary": "有分析称人工智能将在三年内取代九成以上新闻编辑岗位，引发行业恐慌。",
        "content": (
            "<p>惊爆！某国际咨询机构最新报告指出，随着大语言模型在内容生成领域的快速迭代，预计到2029年，超过90%的新闻编辑岗位将被AI取代。</p>"
            "<p>报道称，目前AI已经能够独立完成体育赛事快讯、财报摘要、天气预警等模板化新闻写作，且效率和准确性均超过人类编辑。该机构预测，未来三年内，AI内容生成市场将增长500%。</p>"
            "<p>消息一出，多家媒体内部出现恐慌情绪。但国内主流媒体负责人表示，AI目前仍无法替代深度调查报道和时事评论，该报告存在夸大成分。</p>"
        ),
        "category_id": 5, "topic": "人工智能技术发展",
        "source": "自媒体速递", "editor": "演示编辑",
        "tags": _tags(["AI", "标题党", "新闻行业", "演示待审"]),
    },
    # ── 内容过短新闻 ──
    {
        "title": f"{TITLE_PREFIX} 今天天气不错",
        "summary": "今天天气不错。",
        "content": "<p>今天天气不错，适合出去玩。</p>",
        "category_id": 3, "topic": None,
        "source": "个人投稿", "editor": "演示编辑",
        "tags": _tags(["天气", "演示待审"]),
    },
    # ── 信息不完整新闻（缺少来源、具体信息）──
    {
        "title": f"{TITLE_PREFIX} 某城市即将推行全域无人驾驶出租车",
        "summary": "据悉，某城市将在下月起全面开放无人驾驶出租车运营，但该报道未提供具体城市名称和时间表。",
        "content": (
            "<p>据知情人士透露，国内某一线城市将在近期全面开放无人驾驶出租车商业运营。据悉，该计划涉及多个自动驾驶企业，初期将投放数百辆无人驾驶出租车。</p>"
            "<p>报道中未提及具体城市名称、开放时间、运营区域和监管部门审批情况，也未引用任何官方来源或政策文件。</p>"
        ),
        "category_id": 5, "topic": "新能源汽车与智能交通",
        "source": "", "editor": "演示编辑",
        "tags": _tags(["无人驾驶", "智能交通", "信息不完整", "演示待审"]),
    },
    # ── 可能含敏感词或争议表达 ──
    {
        "title": f"{TITLE_PREFIX} 某地就业数据引发争议，统计口径遭质疑",
        "summary": "报道称某地区就业统计数据显示异常，引发公众对数据真实性的质疑，文中使用了较为情绪化的表述。",
        "content": (
            "<p>近日有网友爆料称，某地区公布的就业率数据与当地居民实际感受存在巨大差异。</p>"
            "<p>爆料者指出，该地区将灵活就业、临时性工作全部计入就业人口统计，导致就业率数据虚高。部分居民在接受采访时表示统计数据好看但身边找工作依然困难。</p>"
            "<p>报道情绪化表达较多，使用了较为强烈的措辞，需审核确认事实依据和数据来源。</p>"
        ),
        "category_id": 3, "topic": "高校毕业生就业形势",
        "source": "社会观察网", "editor": "演示编辑",
        "tags": _tags(["就业", "数据争议", "需核实", "演示待审"]),
    },
    # ── 重复/高度相似新闻（与第一条题材高度相似）──
    {
        "title": f"{TITLE_PREFIX} 多家企业集中推出行业专用AI助手，大模型进入应用深水区",
        "summary": "多家互联网巨头近日密集发布面向垂直行业的AI助手产品，大模型从通用走向专用。",
        "content": (
            "<p>2026年上半年，国内科技巨头纷纷推出行业专用AI助手。百度发布了面向金融行业的智能分析助手，阿里推出了医疗辅助诊断系统，腾讯则发布了法律文书智能生成平台。</p>"
            "<p>这些行业AI助手均基于各公司自有大模型进行微调训练，针对行业特定需求进行了优化。与通用AI助手相比，行业专用版本在专业术语理解和行业知识问答方面表现更好。</p>"
        ),
        "category_id": 5, "topic": "人工智能技术发展",
        "source": "技术前沿", "editor": "演示编辑",
        "tags": _tags(["大模型", "行业应用", "科技企业", "演示待审"]),
    },
    # ── AI生成痕迹明显 ──
    {
        "title": f"{TITLE_PREFIX} 科技创新引领未来发展新趋势观察与分析",
        "summary": "在当前快速发展的时代背景下，科技创新正成为引领未来发展的重要驱动力，对经济社会各领域产生深远影响。",
        "content": (
            "<p>首先，科技创新的重要性不言而喻。在全球化竞争日益激烈的背景下，科技创新已成为各国竞争力的核心要素。我们需要充分认识到科技创新对经济社会发展的重要推动作用。</p>"
            "<p>其次，科技创新的驱动因素包括政策支持、资金投入、人才培养和产学研协同等多个方面。这些因素相互作用，共同推动科技创新不断向前发展。</p>"
            "<p>最后，科技创新的未来发展趋势主要表现为智能化、绿色化和融合化三大方向。我们需要紧跟时代步伐，把握发展机遇，积极应对挑战。</p>"
            "<p>综上所述，科技创新对未来发展具有重要意义，需要社会各界的共同努力和持续投入。</p>"
        ),
        "category_id": 5, "topic": None,
        "source": "AI生成测试", "editor": "演示编辑",
        "tags": _tags(["AI痕迹", "科技创新", "演示待审"]),
    },
    # ── 科技·人工智能话题 ──
    {
        "title": f"{TITLE_PREFIX} 智能新闻摘要系统准确率突破90%，AI编辑能力再升级",
        "summary": "最新评测显示，基于大语言模型的智能新闻摘要系统在多项评测指标上首次突破90%准确率，标志着AI新闻处理能力达到新水平。",
        "content": (
            "<p>中国信通院近日发布《2026年智能新闻处理技术评测报告》。报告显示，参评的多个智能新闻摘要系统在摘要准确性、关键信息保留率和语言流畅度等核心指标上均取得了显著提升。</p>"
            "<p>其中，基于最新大语言模型技术的摘要系统在事实一致性评测中首次突破90%准确率，较去年提升了约15个百分点。评测专家指出，这一进步意味着AI生成的新闻摘要已经具备了较高的参考价值。</p>"
            "<p>但报告同时指出，AI在深度分析、观点提炼和价值观判断方面仍有明显不足，人类编辑的核心地位短期内不会改变。</p>"
        ),
        "category_id": 5, "topic": "人工智能技术发展",
        "source": "信通院评测", "editor": "演示编辑",
        "tags": _tags(["AI摘要", "新闻处理", "评测", "演示待审"]),
    },
    # ── 财经·AI概念 ──
    {
        "title": f"{TITLE_PREFIX} A股三大指数集体收涨，AI概念股持续活跃",
        "summary": "今日A股市场三大指数全线上涨，人工智能概念板块延续强势表现，北向资金净流入超百亿元。",
        "content": (
            "<p>7月2日，A股三大指数集体收涨。截至收盘，沪指涨0.85%报3256.78点，深成指涨1.26%，创业板指涨1.58%。两市成交额再度突破万亿元。</p>"
            "<p>盘面上，人工智能概念股持续活跃，多只个股涨停。半导体、算力、数据要素等板块涨幅居前，市场做多情绪浓厚。</p>"
            "<p>北向资金今日净流入约120亿元，为近一个月来单日最大净流入额。分析人士指出，市场对AI产业政策的乐观预期是推动资金流入的主要原因。</p>"
        ),
        "category_id": 4, "topic": "人工智能技术发展",
        "source": "财经日报", "editor": "演示编辑",
        "tags": _tags(["A股", "AI概念", "财经", "演示待审"]),
    },
    # ── 社会·高校毕业生就业 ──
    {
        "title": f"{TITLE_PREFIX} 2026届高校毕业生就业率同比回升，新业态成吸纳就业主力",
        "summary": "教育部最新数据显示，2026届高校毕业生就业率同比回升2.3个百分点，平台经济、AI服务等新业态成为吸纳毕业生就业的重要渠道。",
        "content": (
            "<p>教育部高校学生司今日发布2026届高校毕业生就业统计数据显示，截至6月底，2026届高校毕业生总体就业率同比回升2.3个百分点。</p>"
            "<p>从就业去向看，制造业、信息技术服务业、科研技术服务业吸纳毕业生人数位居前三。值得注意的是，平台经济、AI数据服务、内容审核等新业态岗位占比首次超过15%，成为吸纳就业的重要增量来源。</p>"
            "<p>教育部表示，将继续推进访企拓岗专项行动，并鼓励高校毕业生到基层和中西部地区就业创业。</p>"
        ),
        "category_id": 3, "topic": "高校毕业生就业形势",
        "source": "教育新闻网", "editor": "演示编辑",
        "tags": _tags(["就业", "高校毕业生", "新业态", "演示待审"]),
    },
    # ── 体育·体育赛事 ──
    {
        "title": f"{TITLE_PREFIX} 中国女排在世界联赛中取得三连胜，晋级形势乐观",
        "summary": "在世界女排联赛最新一轮比赛中，中国女排直落三局击败对手，取得三连胜，晋级总决赛形势乐观。",
        "content": (
            "<p>北京时间7月2日晚，在世界女排联赛分站赛中，中国女排以3比0击败荷兰女排，取得三连胜。</p>"
            "<p>本场比赛，中国女排在发球、拦网和防守环节表现稳健，主攻手发挥出色拿下全场最高的22分。教练组在赛后表示，球队的配合默契度和战术执行力正在逐步提升。</p>"
            "<p>凭借本场胜利，中国女排在积分榜上跃升至第四位，晋级总决赛前景乐观。接下来球队将迎战意大利女排。</p>"
        ),
        "category_id": 6, "topic": "体育赛事与体育产业",
        "source": "体育快报", "editor": "演示编辑",
        "tags": _tags(["女排", "体育赛事", "世界联赛", "演示待审"]),
    },
    # ── 社会·极端天气 ──
    {
        "title": f"{TITLE_PREFIX} 南方多地遭遇持续强降雨，应急响应提升至三级",
        "summary": "中央气象台发布暴雨橙色预警，南方多省份遭遇持续强降雨天气，部分地区启动防汛三级应急响应。",
        "content": (
            "<p>中央气象台7月2日18时继续发布暴雨橙色预警：预计未来48小时，江南、华南及西南地区东部将出现大到暴雨，局地大暴雨。</p>"
            "<p>受持续强降雨影响，湖南、江西、福建等省份部分河流出现超警戒水位。多地已启动防汛三级应急响应，紧急转移安置群众约5万人。</p>"
            "<p>气象专家提醒，本轮降雨持续时间长、累计雨量大、致灾风险高，需加强防范城市内涝、山洪地质灾害和中小河流洪水。</p>"
        ),
        "category_id": 3, "topic": "极端天气与防灾减灾",
        "source": "气象新闻网", "editor": "演示编辑",
        "tags": _tags(["极端天气", "强降雨", "防汛", "演示待审"]),
    },
]


def seed_pending_news(c, user_ids, topic_name_map) -> int:
    count = 0
    for i, item in enumerate(PENDING_NEWS):
        if _exists(c, "news", "title = %s", [item["title"]]):
            continue

        # Resolve topic_id from topic name
        tid = None
        if item["topic"]:
            c.execute("SELECT id FROM news_topic WHERE topic_name = %s LIMIT 1", [item["topic"]])
            row = c.fetchone()
            tid = int(row[0]) if row else None

        # Unique source_url to avoid UK conflict
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        source_url = f"https://demo-pending.example.com/news_{i}_{ts}"

        publish_time = _rand_date(7)

        c.execute(
            """INSERT INTO news
               (title, summary, content, cover_image, category_id, topic_id,
                source, editor, publish_time, source_url,
                view_count, like_count, comment_count, favorite_count,
                tags, status, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,3,%s,%s)""",
            [
                item["title"], item["summary"], item["content"], "",
                item["category_id"], tid,
                item["source"], item["editor"],
                publish_time, source_url,
                0, 0, 0, 0,
                item["tags"],
                publish_time, publish_time,
            ],
        )
        count += 1
    print(f"  news: inserted {count} pending review items")
    return count


# ═════════════════════════════════════════════════════════════════════
# 4. 待审核社区帖子 (10条)
# ═════════════════════════════════════════════════════════════════════

PENDING_POSTS = [
    # 正常讨论帖
    {
        "title": f"{TITLE_PREFIX} 大家觉得AI生成的新闻摘要真的能替代人工阅读吗？",
        "content": (
            f"{CONTENT_MARKER}\n\n"
            "最近用了几次新闻详情页的AI摘要功能，对于长新闻确实能快速了解大意。\n"
            "但有些深度报道的细节和语气是摘要体现不出来的。想问问大家，\n"
            "你们会完全依赖AI摘要来判断是否阅读原文吗？还是只看摘要就够了？"
        ),
        "topic": "人工智能技术发展",
    },
    # 新闻观点讨论帖
    {
        "title": f"{TITLE_PREFIX} 关于极端天气频发那篇报道，我觉得预警机制还需要完善",
        "content": (
            f"{CONTENT_MARKER}\n\n"
            "刚看到那条关于南方强降雨的新闻，橙色预警发了但感觉很多人不太当回事。\n"
            "我觉得预警信息不仅要发，还要告诉大家具体应该怎么做。\n"
            "比如哪个区域风险最高、最近的避难所在哪里、怎么准备应急物资。\n"
            "新闻媒体在报道极端天气时，能不能加上这些实用信息？"
        ),
        "topic": "极端天气与防灾减灾",
    },
    # 含争议观点但可审核通过
    {
        "title": f"{TITLE_PREFIX} 说实话，我觉得现在AI写作比部分小编写得好了",
        "content": (
            f"{CONTENT_MARKER}\n\n"
            "最近对比了几篇AI生成的文章和人工写作的内容，感觉AI在信息密度、\n"
            "语言规范性和多角度覆盖上已经超过了不少小编。当然AI缺乏真正的观点，\n"
            "但对于信息类报道，AI写的东西确实够用了。这会不会导致大量编辑失业？"
        ),
        "topic": "人工智能技术发展",
    },
    # 含广告推广倾向
    {
        "title": f"{TITLE_PREFIX} 强烈推荐这款AI写作工具，用了三天阅读量翻倍",
        "content": (
            f"{CONTENT_MARKER}\n\n"
            "最近发现了一款超级好用的AI写作工具——超级写作大师！\n"
            "用了三天，我的公众号阅读量从200涨到了2000！\n"
            "现在限时优惠只要99元/月，点击链接注册立减50元！\n"
            "https://example.com/ai-writer-promo\n"
            "真的强烈推荐给大家！"
        ),
        "topic": None,
    },
    # 含引战/低质量表达
    {
        "title": f"{TITLE_PREFIX} 用某品牌手机的人都是交智商税，不服来辩",
        "content": (
            f"{CONTENT_MARKER}\n\n"
            "我真的服了，还有人花一万多买某品牌手机？\n"
            "配置拉胯、系统难用、价格还死贵，买这手机的人不是脑子有坑就是钱多烧的。\n"
            "同样的价格买个其他品牌不香吗？欢迎大家来喷我，反正我说的都是事实！"
        ),
        "topic": None,
    },
    # 内容过短
    {
        "title": f"{TITLE_PREFIX} 好的",
        "content": f"{CONTENT_MARKER}\n\n好的，我知道了。",
        "topic": None,
    },
    # 与智能交通话题相关
    {
        "title": f"{TITLE_PREFIX} 智能交通真的能解决城市拥堵吗？看了新闻有感",
        "content": (
            f"{CONTENT_MARKER}\n\n"
            "看完那篇智能交通的报道，我觉得现在的智能交通系统还只是在治标阶段。\n"
            "比如红绿灯智能调度、拥堵路段实时提醒，这些确实能缓解一些压力。\n"
            "但要真正解决拥堵，可能还需要配合城市规划、公共交通和共享出行。\n"
            "大家觉得智能交通的下一个突破点会在哪里？"
        ),
        "topic": "新能源汽车与智能交通",
    },
    # 文旅消费话题
    {
        "title": f"{TITLE_PREFIX} 暑期文旅消费数据出来了，你们贡献了多少？",
        "content": (
            f"{CONTENT_MARKER}\n\n"
            "今天看到文旅部发布的暑期消费数据，国内旅游人次和消费额都创了新高。\n"
            "我上周刚去了趟云南，七天花了大概8000块。\n"
            "感觉现在大家旅游消费意愿确实很强，但热门景点人太多了体验不太好。\n"
            "大家暑期有出游计划吗？准备去哪里玩？"
        ),
        "topic": "文旅消费与假日经济",
    },
    # 就业话题讨论
    {
        "title": f"{TITLE_PREFIX} 2026届毕业生来说说，你们找到工作了吗？",
        "content": (
            f"{CONTENT_MARKER}\n\n"
            "看到那条高校毕业生就业率的新闻，感觉官方数据跟自己身边的情况有点出入。\n"
            "我周围好多同学到现在还没确定去向，考研二战、考公、gap year的都不少。\n"
            "当然也有去了大厂和国企的，但感觉比例没有数据说的那么高。\n"
            "有没有今年毕业的来说说真实情况？"
        ),
        "topic": "高校毕业生就业形势",
    },
    # 新闻真实性讨论
    {
        "title": f"{TITLE_PREFIX} 如何分辨AI生成的假新闻？分享几个实用技巧",
        "content": (
            f"{CONTENT_MARKER}\n\n"
            "现在AI生成内容越来越逼真，假新闻也越来越多。分享几个辨别技巧：\n"
            "1. 看来源：没有明确来源或来源不可追溯的新闻要警惕。\n"
            "2. 看细节：AI生成的内容往往缺乏具体的时间、地点、人物等信息。\n"
            "3. 交叉验证：对关键信息多搜索几个来源对比。\n"
            "4. 看情绪：标题党、情绪化表达过多的内容大概率有问题。\n"
            "大家还有什么好的辨别方法吗？"
        ),
        "topic": "AI生成内容与谣言识别",
    },
]


def seed_pending_posts(c, user_ids, topic_name_map) -> int:
    count = 0
    for item in PENDING_POSTS:
        if _exists(c, "community_post", "title = %s", [item["title"]]):
            continue

        user_id = random.choice(user_ids)

        tid = None
        if item["topic"]:
            c.execute("SELECT id FROM news_topic WHERE topic_name = %s LIMIT 1", [item["topic"]])
            row = c.fetchone()
            tid = int(row[0]) if row else None

        create_time = _rand_date(7)
        tags = _tags(["演示待审", item["topic"] or "讨论"])

        c.execute(
            """INSERT INTO community_post
               (user_id, title, content, related_news_id, topic_id, tags,
                like_count, comment_count, favorite_count, view_count, heat_score,
                status, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,3,%s,%s)""",
            [
                user_id, item["title"], item["content"],
                None, tid, tags,
                0, 0, 0, 0, 0,
                create_time, create_time,
            ],
        )
        count += 1
    print(f"  community_post: inserted {count} pending review items")
    return count


# ═════════════════════════════════════════════════════════════════════
# 5. 待审核新闻评论 (20条)
# ═════════════════════════════════════════════════════════════════════

PENDING_NEWS_COMMENTS = [
    # 正常评论
    (f"{CONTENT_MARKER} 这条报道很全面，把AI在行业的应用场景梳理得很清楚。希望后续能跟进落地案例。", "normal"),
    (f"{CONTENT_MARKER} 数据翔实，分析到位。建议后续可以增加国际对比的部分。", "normal"),
    (f"{CONTENT_MARKER} 作为从业者，感觉文章中提到的大模型应用确实是我们正在做的事情。", "normal"),
    # 情绪化评论
    (f"{CONTENT_MARKER} 太让人气愤了！这种统计数据问题居然还在发生！必须严查到底！", "emotional"),
    (f"{CONTENT_MARKER} 看到这个新闻我真的无语了，这么多年了一点进步都没有？", "emotional"),
    # 低质量评论
    (f"{CONTENT_MARKER} 沙发！", "low_quality"),
    (f"{CONTENT_MARKER} 顶一下，好文章！", "low_quality"),
    (f"{CONTENT_MARKER} mark，收藏了。", "low_quality"),
    # 广告评论
    (f"{CONTENT_MARKER} 需要AI写作工具的可以加我微信 ai_writer_vip，限时优惠！", "ad"),
    (f"{CONTENT_MARKER} 推荐一个好用的炒股软件，点击链接免费领取：https://example.com/stock-promo", "ad"),
    # 疑似谣言评论
    (f"{CONTENT_MARKER} 据我内部消息，其实这家公司已经快倒闭了，这篇报道是公关稿。", "rumor"),
    (f"{CONTENT_MARKER} 我听说真实数据根本不是这样，这份报告被人篡改过。", "rumor"),
    # 人身攻击评论
    (f"{CONTENT_MARKER} 写这篇报道的编辑水平也太差了吧？这种垃圾文章也好意思发出来？", "attack"),
    (f"{CONTENT_MARKER} 楼上那个评论者是不是脑子有问题？不懂装懂还在这瞎评论。", "attack"),
    # 观点争议但不违规
    (f"{CONTENT_MARKER} 我不同意文章的观点。AI目前的能力被过度夸大了，实际落地效果远没有宣传的那么好。", "controversial"),
    (f"{CONTENT_MARKER} 文章只说了一面，其实AI行业的泡沫也不小。很多所谓AI公司根本没有核心技术。", "controversial"),
    # 与具体新闻内容相关
    (f"{CONTENT_MARKER} 我是学计算机的，看到这篇关于AI的报道觉得很有共鸣。课堂上学的东西真的能用上。", "relevant"),
    (f"{CONTENT_MARKER} 作为气象工作者，想补充一点：橙色预警已经是很高的级别了，大家一定要重视！", "relevant"),
    # 回复型评论（需要父评论）
    (f"{CONTENT_MARKER} 同意你的观点，但我觉得AI在新闻行业的应用还需要更谨慎一些。", "reply"),
    (f"{CONTENT_MARKER} 补充一下，之前有研究显示AI摘要可能引入事实性错误，人工复核很有必要。", "reply"),
]


def seed_pending_news_comments(c, user_ids, all_news_ids) -> int:
    count = 0
    for content, scenario in PENDING_NEWS_COMMENTS:
        if _exists(c, "news_comment", "content = %s AND status = 3", [content]):
            continue

        news_id = random.choice(all_news_ids) if all_news_ids else 1
        user_id = random.choice(user_ids)
        parent_id = None

        # Reply-type: attach to an existing top-level comment on the same news
        if scenario == "reply":
            parents = _fetch_ids(c, "news_comment", "id",
                                 "news_id = %s AND parent_id IS NULL AND status = 1", [news_id])
            if parents:
                parent_id = random.choice(parents)

        create_time = _rand_date(7)

        c.execute(
            """INSERT INTO news_comment
               (news_id, user_id, parent_id, content, like_count, status, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, 3, %s, %s)""",
            [news_id, user_id, parent_id, content, random.randint(0, 5),
             create_time, create_time],
        )
        count += 1
    print(f"  news_comment: inserted {count} pending review items")
    return count


# ═════════════════════════════════════════════════════════════════════
# 6. 待审核帖子评论 (20条)
# ═════════════════════════════════════════════════════════════════════

PENDING_POST_COMMENTS = [
    # 正常回复
    (f"{CONTENT_MARKER} 楼主的分析很有道理，我也觉得AI在新闻行业的应用前景广阔。", "normal"),
    (f"{CONTENT_MARKER} 补充一点，目前已经有媒体在用AI写财报新闻了，效率和准确率都不错。", "normal"),
    (f"{CONTENT_MARKER} 同意，预警信息确实应该更具体一些，不能只发个预警就完事了。", "normal"),
    # 争议回复
    (f"{CONTENT_MARKER} 不太同意楼主的观点。AI目前的能力被严重高估了，很多演示场景和实际落地差距很大。", "dispute"),
    (f"{CONTENT_MARKER} 你说的那个例子其实有偏差，我查了一下原始数据不是这样的。", "dispute"),
    # 广告回复
    (f"{CONTENT_MARKER} 需要代写论文、作业的同学可以联系我，质量保证价格优惠！", "ad"),
    (f"{CONTENT_MARKER} 点击链接领取免费炒股课程：https://example.com/stock-course", "ad"),
    # 灌水回复
    (f"{CONTENT_MARKER} 顶顶顶！好帖必须要顶起来让更多人看到！", "spam"),
    (f"{CONTENT_MARKER} +1，路过看看。", "spam"),
    (f"{CONTENT_MARKER} 哈哈哈哈哈哈哈", "spam"),
    (f"{CONTENT_MARKER} 6666666666", "spam"),
    (f"{CONTENT_MARKER} 楼主说的对！", "spam"),
    # 引战回复
    (f"{CONTENT_MARKER} 就这？这也好意思发出来讨论？楼主水平不行啊。", "flame"),
    (f"{CONTENT_MARKER} 懂的自然懂，不懂的说再多也没用，你们这些喷子就别回复了。", "flame"),
    # 理性反驳
    (f"{CONTENT_MARKER} 我觉得可以从另一个角度看这个问题。AI确实能提高信息处理效率，但新闻行业的核心竞争力在于深度调查和独家报道，这是AI无法替代的。AI工具应该是辅助而不是替代。", "rational"),
    (f"{CONTENT_MARKER} 你的观点有一定道理，但忽略了一个关键因素：数据质量。如果输入的数据本身就有偏差，AI的输出也会有问题。所以关键还是要提高数据质量。", "rational"),
    # 内容补充
    (f"{CONTENT_MARKER} 之前看到过类似分析报告，其中提到2025年AI生成内容占比已经达到30%，预计2028年将超过50%。这个趋势确实值得关注。", "supplement"),
    (f"{CONTENT_MARKER} 关于极端天气预警，推荐大家用国家预警信息中心的官方APP，可以实时收到本地预警通知。", "supplement"),
    # 多级回复
    (f"{CONTENT_MARKER} 回复层主：你提到的数据来源是哪里？我看到的版本不一样。", "reply"),
    (f"{CONTENT_MARKER} 对楼上补充一点，确实有研究显示AI摘要的事实错误率在5%左右，人工复核很有必要。", "reply"),
]


def seed_pending_post_comments(c, user_ids, all_post_ids) -> int:
    count = 0
    for content, scenario in PENDING_POST_COMMENTS:
        if _exists(c, "post_comment", "content = %s AND status = 3", [content]):
            continue

        post_id = random.choice(all_post_ids) if all_post_ids else 1
        user_id = random.choice(user_ids)
        parent_id = None

        if scenario == "reply":
            parents = _fetch_ids(c, "post_comment", "id",
                                 "post_id = %s AND parent_id IS NULL AND status = 1", [post_id])
            if parents:
                parent_id = random.choice(parents)

        create_time = _rand_date(7)

        c.execute(
            """INSERT INTO post_comment
               (post_id, user_id, parent_id, content, like_count, status, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, 3, %s, %s)""",
            [post_id, user_id, parent_id, content, random.randint(0, 3),
             create_time, create_time],
        )
        count += 1
    print(f"  post_comment: inserted {count} pending review items")
    return count


# ═════════════════════════════════════════════════════════════════════
# 清理函数
# ═════════════════════════════════════════════════════════════════════


def cleanup() -> None:
    """删除本脚本插入的所有演示数据。

    通过 TITLE_PREFIX / CONTENT_MARKER / USER_PREFIX 匹配删除，
    不影响已有真实数据。
    """
    conn = get_conn()
    try:
        with conn.cursor() as c:
            # Order matters: delete comments before their parent content
            nc1 = c.execute(
                "DELETE FROM news_comment WHERE content LIKE %s", [f"%{CONTENT_MARKER}%"]
            )
            pc1 = c.execute(
                "DELETE FROM post_comment WHERE content LIKE %s", [f"%{CONTENT_MARKER}%"]
            )
            n1 = c.execute(
                "DELETE FROM news WHERE title LIKE %s", [f"%{TITLE_PREFIX}%"]
            )
            p1 = c.execute(
                "DELETE FROM community_post WHERE title LIKE %s", [f"%{TITLE_PREFIX}%"]
            )
            u1 = c.execute(
                "DELETE FROM user WHERE username LIKE %s", [f"{USER_PREFIX}%"]
            )
            conn.commit()
            print(f"Cleanup completed ({TITLE_PREFIX}):")
            print(f"  news:               {n1} rows deleted")
            print(f"  community_post:     {p1} rows deleted")
            print(f"  news_comment:       {nc1} rows deleted")
            print(f"  post_comment:       {pc1} rows deleted")
            print(f"  user:               {u1} rows deleted")
    except Exception as exc:
        conn.rollback()
        print(f"Cleanup error: {exc}", file=sys.stderr)
        raise
    finally:
        conn.close()


# ═════════════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════════════


def main() -> None:
    print("=" * 60)
    print("后台待审核中心演示数据种子脚本")
    print(f"标记前缀: {TITLE_PREFIX}")
    print("=" * 60)

    conn = get_conn()
    try:
        with conn.cursor() as c:
            # ── Gather existing reference data ──
            existing_news_ids = _fetch_ids(c, "news", "id", "status = 1")
            existing_post_ids = _fetch_ids(c, "community_post", "id", "status = 1")
            print(f"Existing reference data: {len(existing_news_ids)} news, {len(existing_post_ids)} posts")

            # Build topic_name→id map
            c.execute("SELECT id, topic_name FROM news_topic WHERE status = 1")
            topic_name_map = {row[1]: int(row[0]) for row in c.fetchall()}
            print(f"Available topics: {list(topic_name_map.keys())}")

            # ── Step 1: Test users ──
            user_ids = seed_test_users(c)
            conn.commit()

            # ── Step 2: Additional topics ──
            seed_topics(c)
            # Refresh topic map after inserts
            c.execute("SELECT id, topic_name FROM news_topic WHERE status = 1")
            topic_name_map = {row[1]: int(row[0]) for row in c.fetchall()}
            conn.commit()

            # ── Step 3: Pending news ──
            n1 = seed_pending_news(c, user_ids, topic_name_map)
            conn.commit()

            # ── Step 4: Pending posts ──
            n2 = seed_pending_posts(c, user_ids, topic_name_map)
            conn.commit()

            # ── Step 5: Pending news comments ──
            n3 = seed_pending_news_comments(c, user_ids, existing_news_ids)
            conn.commit()

            # ── Step 6: Pending post comments ──
            n4 = seed_pending_post_comments(c, user_ids, existing_post_ids)
            conn.commit()

        total = n1 + n2 + n3 + n4
        print("─" * 60)
        print(f"总计插入: {total} 条待审核数据（status=3）")
        print(f"  news_comment:       {n3}")
        print(f"  post_comment:       {n4}")
        print(f"  news:               {n1}")
        print(f"  community_post:     {n2}")
        print(f"所有数据标记: {TITLE_PREFIX} / {CONTENT_MARKER}")
        print("=" * 60)

    except Exception as exc:
        conn.rollback()
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
