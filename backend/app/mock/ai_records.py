"""AI 生成历史记录 Mock 数据。"""

from datetime import datetime, timedelta

MOCK_AI_RECORDS = [
    {
        "id": 3,
        "source": "manual",
        "source_news_id": None,
        "source_title": "用户自输入",
        "input_text": "区块链技术在供应链中的应用越来越广泛。许多企业开始采用区块链来确保产品的真伪和溯源。这项技术提高了透明度，减少了欺诈行为。",
        "params": {
            "title_count": 3,
            "summary_type": "generate",
            "summary_style": "简明扼要",
            "title_style": "客观新闻型",
            "summary_length": "both",
        },
        "result": {
            "candidate_titles": [
                "区块链技术在供应链中应用拓展",
                "企业采用区块链确保产品真伪",
                "区块链提高供应链透明度",
            ],
            "summary_short": "本文介绍了区块链在供应链中的应用发展。",
            "summary_long": "本文详细介绍了区块链、供应链、企业在供应链中的最新应用。区块链技术在供应链中的应用越来越广泛，许多企业采用该技术以确保产品真伪。这项技术的应用有助于推动供应链的进一步发展。",
            "summary_points": [
                "区块链应用于供应链领域不断拓展",
                "企业通过区块链实现产品溯源",
                "区块链提高透明度减少欺诈",
            ],
            "keywords": ["区块链", "供应链", "产品", "溯源", "透明度"],
            "elements": {
                "who": "相关企业",
                "what": "区块链应用于供应链",
                "when": "近期",
                "where": "相关地区",
                "why": "确保产品真伪和溯源",
                "how": "采用区块链技术",
            },
            "consistency": {
                "score": 88,
                "risk_level": "low",
                "issues": [],
                "suggestions": ["内容结构完整"],
            },
        },
        "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
        "title_count": 3,
        "risk_level": "low",
    },
    {
        "id": 2,
        "source": "news",
        "source_news_id": 5,
        "source_title": "中国科学家在量子计算领域取得新突破",
        "input_text": "我国科研团队在量子计算领域取得重要突破。研究成果将推动量子计算从实验研究向实际应用迈进。",
        "params": {
            "title_count": 5,
            "summary_type": "extract",
            "summary_style": "客观正式",
            "title_style": "吸引点击型",
            "summary_length": "short",
        },
        "result": {
            "candidate_titles": [
                "震撼！科研团队竟然这样突破量子计算",
                "科研团队突然宣布量子计算重大决策",
                "万万没想到，科研团队居然...",
                "量子计算领域爆出惊人新闻",
                "都惊呆了！科研团队最新动向曝光",
            ],
            "summary_short": "我国科研团队在量子计算领域取得重要突破。",
            "summary_long": "",
            "summary_points": [
                "科研团队在量子计算领域取得突破",
                "成果将推动量子计算应用发展",
            ],
            "keywords": ["科研", "量子计算", "突破", "团队"],
            "elements": {
                "who": "科研团队",
                "what": "在量子计算领域取得重要突破",
                "when": "近期",
                "where": "相关地区",
                "why": "为了推进科研的发展",
                "how": "通过相关措施或行动推进",
            },
            "consistency": {
                "score": 72,
                "risk_level": "medium",
                "issues": ["输入正文较短，摘要依据有限"],
                "suggestions": ["建议输入更多的新闻正文内容"],
            },
        },
        "created_at": (datetime.now() - timedelta(hours=6)).isoformat(),
        "title_count": 5,
        "risk_level": "medium",
    },
    {
        "id": 1,
        "source": "news",
        "source_news_id": 3,
        "source_title": "教育改革取得明显成效，学生核心素养得到提升",
        "input_text": "教育改革取得明显成效，学生核心素养得到提升。学校推行素质教育模式，减少学生课业负担。家长和教师普遍反映，学生的学习兴趣明显增加。",
        "params": {
            "title_count": 3,
            "summary_type": "generate",
            "summary_style": "简明扼要",
            "title_style": "客观新闻型",
            "summary_length": "both",
        },
        "result": {
            "candidate_titles": [
                "教育改革取得重要进展",
                "教育改革相关新动态曝光",
                "我国教育改革发展迎来新机遇",
            ],
            "summary_short": "本文介绍了教育改革的成效和学生素养提升。",
            "summary_long": "本文详细介绍了教育、学生、学校的最新发展。教育改革取得明显成效，学生核心素养得到提升。学校推行素质教育模式，减少学生课业负担。这些改革有助于推动教育的进一步发展。",
            "summary_points": [
                "教育改革取得明显成效",
                "学生素养和学习兴趣提升",
                "素质教育模式不断推进",
            ],
            "keywords": ["教育", "学生", "改革", "素质", "素养"],
            "elements": {
                "who": "学校和教师",
                "what": "推行素质教育模式，学生素养提升",
                "when": "近期",
                "where": "相关学校",
                "why": "为了推进教育的发展",
                "how": "推行素质教育模式，减少课业负担",
            },
            "consistency": {
                "score": 92,
                "risk_level": "low",
                "issues": [],
                "suggestions": ["文本质量满足生成条件"],
            },
        },
        "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "title_count": 3,
        "risk_level": "low",
    },
]

# 用于存储运行时添加的记录（内存中，不持久化）
_runtime_records = []
_next_id = max([r["id"] for r in MOCK_AI_RECORDS]) + 1


def get_all_records():
    """获取所有历史记录（包括 mock 和运行时添加的）。"""
    return MOCK_AI_RECORDS + _runtime_records


def get_record_by_id(record_id):
    """获取指定 ID 的历史记录。"""
    all_records = get_all_records()
    for record in all_records:
        if record["id"] == record_id or record["id"] == int(record_id):
            return record
    return None


def add_record(record_data):
    """添加新的历史记录（运行时，不持久化）。"""
    global _next_id
    record = {
        "id": _next_id,
        **record_data,
    }
    _runtime_records.append(record)
    _next_id += 1
    return record


def delete_record(record_id):
    """删除指定 ID 的历史记录。"""
    record_id = int(record_id)
    global _runtime_records

    for i, record in enumerate(MOCK_AI_RECORDS):
        if record["id"] == record_id:
            return False

    for i, record in enumerate(_runtime_records):
        if record["id"] == record_id:
            _runtime_records.pop(i)
            return True

    return False
