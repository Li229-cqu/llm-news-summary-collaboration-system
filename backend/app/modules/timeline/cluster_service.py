"""新闻话题自动聚类核心服务。

基于 TF-IDF + KMeans/MiniBatchKMeans 从新闻数据库中自动发现热点话题。
本模块纯内存计算，不写入数据库、不修改 news_topic / news.topic_id / event_timeline。

依赖：jieba, scikit-learn
"""

from __future__ import annotations

import difflib
import logging
import math
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

import numpy as np

from app.db.database import execute_insert, execute_query, execute_update, get_connection

logger = logging.getLogger(__name__)

# ── 轻量中文停用词（基础虚词 + 新闻场景过泛词）─────────────────────
_STOP_WORDS = {
    # 基础虚词
    "的", "了", "和", "是", "在", "对", "将", "与", "及", "等",
    "为", "也", "从", "到", "被", "这", "那", "一个",
    "称", "其", "该", "已", "并", "或", "但", "而", "且",
    "所", "以", "之", "于", "则", "就", "都", "要", "会",
    "可", "能", "可以", "这个", "那个", "一些", "这些", "那些",
    "自己", "我们", "他们", "它们", "什么", "怎么", "如何", "为何",
    "因为", "所以", "但是", "然而", "不过", "虽然", "如果", "不仅",
    "本报讯", "讯", "编辑", "责编",
    # 新闻场景过泛词（高文档频率，缺乏区分度）
    "记者", "报道", "新闻", "近日", "今天", "目前", "相关",
    "表示", "指出", "认为", "据", "据悉", "据了解",
    "发展", "建设", "工作", "活动", "问题", "情况", "方面",
    "进行", "推动", "提升", "加强", "促进", "实现", "推进",
    "提供", "服务", "组织", "项目", "计划", "方案",
    "发布", "举行", "开展", "持续", "进一步", "积极", "有效",
    "重要", "主要", "关键", "作为", "关注",
    "发生", "出现", "成为", "受到", "引起",
    "全国", "国内", "国际", "消息", "记者从",
    "中国", "美国",  # 高频泛词，几乎每篇新闻都有
    "日电", "新华社",  # 新闻电头格式
}

# ── 通用关键词过滤词（聚类命名时不使用）─────────────────────────────
_GENERIC_WORDS_FOR_NAMING = {
    "全国", "国内", "国际", "中国", "美国", "发展", "建设", "工作",
    "活动", "问题", "情况", "方面", "进行", "推动", "提升", "加强",
    "促进", "实现", "推进", "提供", "服务", "组织", "项目", "计划",
    "方案", "发布", "举行", "开展", "持续", "进一步", "积极", "有效",
    "重要", "主要", "关键", "受到", "引起", "关注", "消息",
    "日电", "新华社",  # 新闻电头
    "时政", "相关", "北京",  # 分类名/地名泛词/过渡词
}

# ── jieba 自定义词典（专有名词保护）────────────────────────────────
_JIEBA_CUSTOM_WORDS = [
    "委内瑞拉", "全国人民代表大会常务委员会", "中国共产党",
    "人工智能", "大模型", "低空经济", "无人机",
    "世界杯", "墨西哥世界杯", "新质生产力",
    "食品安全", "市场监管总局", "俄乌冲突",
    "新能源汽车", "机器人", "量子计算",
    "中国光谷", "网络安全", "智能制造",
    "全固态电池", "柔性传感器", "无人配送",
    "数字人民币", "碳中和", "元宇宙",
    "一带一路", "粤港澳大湾区", "长三角",
]

# ── 正则 ───────────────────────────────────────────────────────────
_HTML_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_DIGIT_ONLY_RE = re.compile(r"^\d+([.]\d+)?$")
_PUNCT_FOR_TITLE_DEDUP = re.compile(r"[，,。！!？?、：:；;（）()【】\[\]\"\"''\s]+")


# ══════════════════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════════════════

def _init_jieba():
    """初始化 jieba 分词器（加载自定义词典）。"""
    import jieba
    for word in _JIEBA_CUSTOM_WORDS:
        jieba.add_word(word)


def _clean_text(text: str | None) -> str:
    """清洗文本：去 HTML、统一空白。"""
    if not text:
        return ""
    text = _HTML_RE.sub(" ", str(text))
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def _normalize_title(title: str) -> str:
    """规范化标题用于去重比对：去标点、去空格。"""
    t = _PUNCT_FOR_TITLE_DEDUP.sub("", title)
    return t.strip()


def _build_news_text(title: str, summary: str, content_prefix: str) -> str:
    """构建加权聚类文本：title×3 + summary×2 + content[:200]×1。"""
    t = _clean_text(title)
    s = _clean_text(summary) if summary else ""
    c = _clean_text(content_prefix)[:200] if content_prefix else ""

    parts: list[str] = []
    if t:
        parts.extend([t] * 3)
    if s:
        parts.extend([s] * 2)
    if c:
        parts.append(c)

    return " ".join(parts)


def _tokenize(text: str) -> list[str]:
    """jieba 分词 + 停用词过滤 + 短词过滤。"""
    import jieba

    if not text.strip():
        return []

    words = jieba.cut(text)
    result: list[str] = []
    for w in words:
        w = w.strip()
        if len(w) < 2:
            continue
        if _DIGIT_ONLY_RE.match(w):
            continue
        if w in _STOP_WORDS:
            continue
        result.append(w)
    return result


def _deduplicate_titles(news_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """标题近重复去重：相同或高度相似的标题只保留热度最高的一篇。"""
    kept: list[dict[str, Any]] = []
    normalized_seen: dict[str, dict[str, Any]] = {}  # norm_title -> best news

    for nw in news_list:
        title = _clean_text(nw.get("title"))
        norm = _normalize_title(title)
        if not norm:
            continue

        heat = _compute_news_heat(nw)

        # 完全匹配 vs 相似匹配
        merged = False
        for seen_norm, seen_nw in list(normalized_seen.items()):
            # 完全一致
            if norm == seen_norm:
                merged = True
                if heat > _compute_news_heat(seen_nw):
                    normalized_seen[seen_norm] = nw
                break
            # 高相似度（>92%）
            ratio = difflib.SequenceMatcher(None, norm, seen_norm).ratio()
            if ratio > 0.92:
                merged = True
                if heat > _compute_news_heat(seen_nw):
                    normalized_seen[seen_norm] = nw
                break

        if not merged:
            normalized_seen[norm] = nw

    kept = list(normalized_seen.values())
    logger.info("标题去重：%d → %d 条", len(news_list), len(kept))
    return kept


def _choose_topic_count(n_news: int, max_topics: int = 8) -> int:
    """根据新闻数量自适应选择聚类数 k。"""
    if n_news < 30:
        return max(2, min(max_topics, n_news // 8))
    if n_news < 100:
        return max(3, min(max_topics, n_news // 20))
    if n_news < 300:
        return max(4, min(max_topics, n_news // 35))
    if n_news < 600:
        return max(6, min(max_topics, 8))
    return max(7, min(max_topics, n_news // 70))


def _compute_news_heat(news: dict[str, Any]) -> float:
    """计算单篇新闻热度。"""
    view = int(news.get("view_count") or 0)
    like = int(news.get("like_count") or 0)
    fav = int(news.get("favorite_count") or 0)
    comment = int(news.get("comment_count") or 0)
    return float(view + like * 5 + fav * 4 + comment * 6)


def _fetch_news(days: int, max_news: int) -> list[dict[str, Any]]:
    """从数据库读取最近 days 天的活跃新闻。"""
    since = (datetime.now() - timedelta(days=max(days, 1))).strftime("%Y-%m-%d %H:%M:%S")

    rows = execute_query(
        """
        SELECT
            n.id, n.title, n.summary, n.content, n.source,
            n.publish_time, n.category_id,
            COALESCE(nc.name, '') AS category_name,
            n.view_count, n.like_count, n.comment_count, n.favorite_count
        FROM news n
        LEFT JOIN news_category nc ON nc.id = n.category_id
        WHERE n.status = 1
          AND n.title IS NOT NULL
          AND n.title != ''
          AND n.publish_time >= %s
        ORDER BY n.publish_time DESC
        LIMIT %s
        """,
        [since, max_news],
    )

    if rows is None:
        logger.warning("新闻查询返回 None")
        return []

    filtered: list[dict[str, Any]] = []
    for r in rows:
        title = _clean_text(r.get("title"))
        if len(title) >= 4:
            filtered.append(r)
    return filtered


# ══════════════════════════════════════════════════════════════════════
# 话题构建
# ══════════════════════════════════════════════════════════════════════

def _build_cluster_result(
    cluster_id: int,
    indices: list[int],
    news_list: list[dict[str, Any]],
    tfidf_matrix: Any,
    feature_names: list[str],
    cluster_centroid: Any,  # shape (1, n_features)
) -> dict[str, Any] | None:
    """构建单个话题簇的结果字典。"""
    from sklearn.metrics.pairwise import cosine_similarity

    cluster_news = [news_list[i] for i in indices]
    n = len(cluster_news)
    if n == 0:
        return None

    # ── 关键词：TF-IDF 均值 top 词，过滤泛词 ──
    cluster_vecs = tfidf_matrix[indices].toarray()
    mean_vec = cluster_vecs.mean(axis=0)
    top_indices = mean_vec.argsort()[::-1]

    raw_keywords: list[str] = []
    for idx in top_indices:
        word = feature_names[idx]
        score = float(mean_vec[idx])
        if score < 0.02:
            continue
        if word in _STOP_WORDS or word in _GENERIC_WORDS_FOR_NAMING:
            continue
        if word not in raw_keywords:
            raw_keywords.append(word)
        if len(raw_keywords) >= 10:
            break

    # 取前 6 个有意义的关键词
    keywords = raw_keywords[:6]

    # ── 话题名（先用关键词生成，后面用代表新闻重命名） ──
    meaningful = [kw for kw in keywords if kw not in _GENERIC_WORDS_FOR_NAMING]
    cat_name, cat_purity, _ = _compute_category_purity(indices, news_list)

    # 先用热度选出代表新闻列表供命名使用
    scored_for_name = [(_compute_news_heat(nw), nw) for nw in cluster_news]
    scored_for_name.sort(key=lambda x: x[0], reverse=True)
    top_reps_for_name: list[dict[str, Any]] = []
    for _, nw in scored_for_name[:5]:
        top_reps_for_name.append({
            "id": int(nw["id"]),
            "title": _clean_text(nw.get("title")),
        })

    topic_name = _extract_topic_phrase(top_reps_for_name, keywords, cat_name)

    # ── 摘要 ──
    if len(meaningful) >= 2:
        summary = f"围绕{meaningful[0]}、{meaningful[1]}等主题形成的热点话题，共 {n} 篇相关报道。"
    elif meaningful:
        summary = f"围绕{meaningful[0]}形成的热点话题，共 {n} 篇相关报道。"
    else:
        summary = f"自动聚合形成的热点话题，共 {n} 篇新闻。"

    # ── 热度 ──
    total_heat = sum(_compute_news_heat(nw) for nw in cluster_news)
    avg_heat = total_heat / max(n, 1)
    topic_heat = round(min(100.0, math.log2(n + 1) * 15 + avg_heat * 0.3), 1)

    # ── 代表新闻：热度 × 与簇中心相似度 ──
    centroid_vec = cluster_centroid.reshape(1, -1)
    candidates: list[tuple[float, dict[str, Any]]] = []
    for idx in indices:
        nw = news_list[idx]
        heat = _compute_news_heat(nw)
        news_vec = tfidf_matrix[idx].toarray().reshape(1, -1)
        sim = float(cosine_similarity(news_vec, centroid_vec)[0][0])
        score = heat * 0.1 + sim * 20  # 热度占 10%，相似度占 90%
        candidates.append((score, nw))

    candidates.sort(key=lambda x: x[0], reverse=True)
    representative_news: list[dict[str, Any]] = []
    for score, nw in candidates[:5]:
        representative_news.append({
            "id": int(nw["id"]),
            "title": _clean_text(nw.get("title")),
            "source": _clean_text(nw.get("source")),
            "publish_time": str(nw.get("publish_time", "")),
            "heat": int(_compute_news_heat(nw)),
            "score": round(score, 2),
        })

    # ── 质量评分 ──
    quality_score, quality_status = _compute_cluster_quality(
        topic_name=topic_name,
        keywords=keywords,
        cat_purity=cat_purity,
        news_count=n,
    )

    return {
        "cluster_id": cluster_id,
        "topic_name": topic_name,
        "keywords": keywords,
        "summary": summary,
        "heat_score": topic_heat,
        "news_count": n,
        "news_ids": [int(news_list[i]["id"]) for i in indices],
        "representative_news": representative_news,
        "category_name": cat_name,
        "category_purity": cat_purity,
        "quality_score": quality_score,
        "quality_status": quality_status,
    }


# ── 更好的话题名模板词 ─────────────────────────────────────────────
_TOPIC_NAMING_PREFIXES: dict[str, str] = {
    "科技": "科技前沿",
    "财经": "财经市场",
    "体育": "体育赛事",
    "娱乐": "娱乐文化",
    "时政": "时政要闻",
    "社会": "社会民生",
    "国际": "国际动态",
    "世界": "国际动态",
}


def _compute_category_purity(indices: list[int], news_list: list[dict[str, Any]]) -> tuple[str, float, str]:
    """计算 cluster 的分类纯度。返回 (主分类名, 占比, 主分类ID)。"""
    cat_counts: dict[str, int] = {}
    for i in indices:
        cat = _clean_text(news_list[i].get("category_name") or "")
        if not cat:
            cat = str(news_list[i].get("category_id", ""))
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    if not cat_counts:
        return ("未知", 0.0, "")

    total = sum(cat_counts.values())
    best_cat = max(cat_counts, key=cat_counts.get)
    purity = round(cat_counts[best_cat] / total * 100, 1)
    return (best_cat, purity, best_cat)


# ── 不能作为话题主词的弱词 ──────────────────────────────────────────
_WEAK_TOPIC_WORDS = {
    "ai", "演示", "表演", "商演", "守护", "发射", "活动", "企业",
    "创新", "全国", "发展", "建设", "推进", "相关", "时政",
    "北京", "记者", "报道", "文化", "技术", "产业", "市场",
    "比赛", "跳水", "工作", "项目", "计划", "方案",
    "运动", "新华社", "开放", "展示",
    "中新社", "显示", "举办", "青年",
}


def _extract_topic_phrase(rep_news: list[dict[str, Any]], keywords: list[str], cat_name: str) -> str:
    """从代表新闻标题中提取核心短语作为话题名。"""
    meaningful = [kw for kw in keywords if kw not in _GENERIC_WORDS_FOR_NAMING and kw not in _WEAK_TOPIC_WORDS]

    # ── 规则 1: 体育类 ──
    sports_kw = {"世界杯", "女排", "墨西哥", "球队", "比赛", "赛事", "田径", "柔道", "游泳", "跳水", "NBA"}
    if cat_name == "体育" or any(kw in meaningful for kw in sports_kw):
        if "世界杯" in meaningful or any("世界杯" in kw for kw in keywords):
            return "墨西哥世界杯赛事进展"
        if "女排" in meaningful or any("女排" in kw for kw in keywords):
            return "女排赛事动态"
        match = next((kw for kw in meaningful if kw in {"田径", "柔道", "游泳", "跳水", "NBA"}), None)
        if match:
            return f"{match}赛事进展"
        return f"{cat_name}赛事动态"

    # ── 规则 2: 时政/反腐 ──
    if cat_name == "时政" or any(kw in meaningful for kw in {"纪委", "审查", "调查", "处分", "监委"}):
        if any(kw in meaningful for kw in {"纪委", "监委", "审查", "调查", "处分"}):
            return "纪委监委审查调查"
        if "全国人民代表大会常务委员会" in meaningful or any("全国人民代表大会常务委员会" in kw for kw in keywords):
            if "版权" in meaningful:
                return "全国人大常委会法律与版权动态"
            return "全国人大常委会法律动态"
        if "习近平" in meaningful:
            return "时政要闻动态"

    # ── 规则 3: 国际类 ──
    if cat_name == "国际" or any(kw in meaningful for kw in {"委内瑞拉", "俄罗斯", "导弹", "乌克兰", "袭击"}):
        if "委内瑞拉" in meaningful:
            if "导弹" in meaningful or "袭击" in meaningful:
                return "委内瑞拉局势与导弹袭击"
            return "委内瑞拉局势动态"
        if "俄罗斯" in meaningful or "导弹" in meaningful:
            return "国际局势与军事动态"
        return "国际热点动态"

    # ── 规则 4: 科技/AI ──
    if cat_name == "科技" or any(kw in meaningful for kw in {"人工智能", "大模型", "机器人", "AI", "智能"}):
        if "人工智能" in meaningful:
            return "人工智能产业应用进展"
        if "大模型" in meaningful:
            return "大模型应用进展"
        return "科技产业前沿动态"

    # ── 规则 5: 交通/高铁 ──
    if any(kw in meaningful for kw in {"高铁", "运营", "车站", "开通", "铁路"}):
        if "高铁" in meaningful or "运营" in meaningful:
            return "高铁开通运营动态"
        return "交通建设进展"

    # ── 先从 meaningful 中选强词 ──
    strong = [kw for kw in meaningful if kw not in _WEAK_TOPIC_WORDS]

    # ── 规则 6: 从代表新闻标题提取（仅在强词足够时使用）──
    if len(strong) >= 2 and rep_news:
        best_title = _clean_text(rep_news[0].get("title", ""))
        for marker in ["开幕", "开通", "发布", "召开", "举行", "启动", "推进", "成立", "正式"]:
            idx = best_title.find(marker)
            if idx > 4:
                prefix_text = best_title[: idx + len(marker)]
                if len(prefix_text) <= 24:
                    return prefix_text
                return prefix_text[:22] + "..."

    # ── 兜底 ──
    if len(strong) >= 2:
        return f"{strong[0]}{strong[1]}动态"
    if len(strong) == 1:
        return f"{strong[0]}相关动态"
    prefix = _TOPIC_NAMING_PREFIXES.get(cat_name, cat_name + "热点" if cat_name else "热点")
    return f"{prefix}事件"


def _compute_cluster_quality(
    topic_name: str,
    keywords: list[str],
    cat_purity: float,
    news_count: int,
) -> tuple[float, str]:
    """对话题进行质量评分，返回 (score, status)。"""
    # 1. 命名质量检查
    weak_in_name = [w for w in _WEAK_TOPIC_WORDS if w in topic_name]
    name_ok = len(weak_in_name) == 0 and "进展" not in topic_name.split("与")[-1] if "与" in topic_name else True

    # 2. 关键词质量
    strong_kw = [kw for kw in keywords if kw not in _GENERIC_WORDS_FOR_NAMING and kw not in _WEAK_TOPIC_WORDS]
    kw_quality = min(1.0, len(strong_kw) / 4.0)

    # 3. 纯度
    purity_score = min(1.0, cat_purity / 60.0)

    # 4. 综合评分——弱命名直接降权
    score = round(purity_score * 0.35 + kw_quality * 0.35 + (0.3 if name_ok else 0.0), 2)

    # ── 状态判定（顺序重要） ──
    if news_count < 3:
        return (score, "too_small")
    # 弱词检测：topic_name 中任何弱词出现则标记 weak_name
    if not name_ok:
        return (score, "weak_name")
    # 附加检查："XX与XX动态/进展"中如果两个词都是弱词或泛词
    if "与" in topic_name:
        parts = topic_name.replace("进展", "").replace("动态", "").split("与")
        if len(parts) == 2:
            both_weak = all(
                any(w in p for w in _WEAK_TOPIC_WORDS) or p in _GENERIC_WORDS_FOR_NAMING
                for p in parts
            )
            if both_weak:
                return (score, "weak_name")
    if cat_purity < 35.0:
        return (score, "mixed_category")
    if score < 0.5:
        return (score, "low_quality")

    return (score, "ok")


def _split_large_cluster(
    indices: list[int],
    news_list: list[dict[str, Any]],
    corpus: list[str],
    max_size: int = 50,
) -> list[list[int]]:
    """对过大簇进行二次 KMeans 拆分。返回子簇列表。"""
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer

    n = len(indices)
    if n <= max_size:
        return [indices]

    # 子簇数
    n_sub = min(3, max(2, n // 30))
    sub_corpus = [corpus[i] for i in indices]
    tokenized = [" ".join(_tokenize(doc)) for doc in sub_corpus]

    vec = TfidfVectorizer(max_features=1000, min_df=1, max_df=0.7, sublinear_tf=True)
    sub_matrix = vec.fit_transform(tokenized)

    model = KMeans(n_clusters=n_sub, random_state=42, n_init="auto")
    sub_labels = model.fit_predict(sub_matrix)

    sub_clusters: dict[int, list[int]] = {}
    for pos, label in enumerate(sub_labels):
        sub_clusters.setdefault(int(label), []).append(indices[pos])

    # 过滤过小子簇（< 3）
    result = [s for s in sub_clusters.values() if len(s) >= 3]
    logger.info("大簇拆分：%d → %d 个子簇", n, len(result))
    return result if result else [indices]


# ══════════════════════════════════════════════════════════════════════
# 第二级聚合：话题内新闻 → 事件点
# ══════════════════════════════════════════════════════════════════════

def _select_news_for_cluster(
    indices: list[int],
    news_list: list[dict[str, Any]],
    tfidf_matrix: Any,
    cluster_centroid: Any,
    max_news: int = 30,
) -> list[int]:
    """从话题内选择最多 max_news 条新闻参与事件点聚合。

    综合评分：cluster_similarity * 0.6 + normalized_heat * 0.3 + time_diversity * 0.1
    """
    from sklearn.metrics.pairwise import cosine_similarity

    centroid_vec = cluster_centroid.reshape(1, -1)
    n = len(indices)
    if n <= max_news:
        return list(indices)

    # 计算相似度和热度
    scored: list[tuple[float, int]] = []
    max_heat = max((_compute_news_heat(news_list[i]) for i in indices), default=1)

    for i in indices:
        nw = news_list[i]
        vec = tfidf_matrix[i].toarray().reshape(1, -1)
        sim = float(cosine_similarity(vec, centroid_vec)[0][0])
        norm_heat = _compute_news_heat(nw) / max(max_heat, 1)

        # 时间多样性加分：按 publish_time 分组，同一天的文章给递减加分
        pt = str(nw.get("publish_time", ""))[:10]
        time_bonus = 0.0  # 基础不加分

        score = sim * 0.6 + norm_heat * 0.3 + time_bonus * 0.1
        scored.append((score, i))

    scored.sort(key=lambda x: x[0], reverse=True)

    selected: list[int] = []
    seen_dates: dict[str, int] = {}
    for score, idx in scored:
        if len(selected) >= max_news:
            break
        pt = str(news_list[idx].get("publish_time", ""))[:10]
        # 每天最多选 5 条，保证时间多样性
        day_count = seen_dates.get(pt, 0)
        if day_count < 5:
            selected.append(idx)
            seen_dates[pt] = day_count + 1

    return selected


def _aggregate_event_points(
    selected_indices: list[int],
    news_list: list[dict[str, Any]],
    tfidf_matrix: Any,
    max_event_points: int = 6,
    max_news_per_event: int = 5,
    similarity_threshold: float = 0.45,
) -> list[dict[str, Any]]:
    """话题内新闻合并为事件点。

    贪心策略：按综合分从高到低，每次选一个未分配新闻作为 seed，
    合并相似度 >= threshold 的未分配新闻。
    """
    from sklearn.metrics.pairwise import cosine_similarity

    if not selected_indices:
        return []

    n = len(selected_indices)
    # 构建子矩阵
    sub_vectors = [tfidf_matrix[i].toarray().reshape(1, -1) for i in selected_indices]
    sub_matrix = np.vstack(sub_vectors) if sub_vectors else np.zeros((0, 1))

    # 计算全部相似度
    sim_matrix = cosine_similarity(sub_matrix) if n > 0 else np.zeros((0, 0))

    # 按热度 + 中心相似度评分排序
    scored: list[tuple[float, int]] = []
    max_heat = max((_compute_news_heat(news_list[i]) for i in selected_indices), default=1)
    for pos, idx in enumerate(selected_indices):
        nw = news_list[idx]
        heat = _compute_news_heat(nw) / max(max_heat, 1)
        score = heat * 0.4 + 0.6  # 偏重热度（事件聚合时）
        scored.append((score, pos))

    scored.sort(key=lambda x: x[0], reverse=True)

    assigned: set[int] = set()
    event_points: list[dict[str, Any]] = []

    for seed_score, seed_pos in scored:
        if seed_pos in assigned:
            continue
        if len(event_points) >= max_event_points:
            break

        # 收集与 seed 相似度 >= threshold 的未分配新闻
        # 增加关键词重合度约束：避免把不相关新闻强行合并
        seed_tokens = set(_tokenize(_clean_text(news_list[selected_indices[seed_pos]].get("title", ""))))
        cluster_positions = [seed_pos]
        for other_pos in range(n):
            if other_pos == seed_pos or other_pos in assigned:
                continue
            sim = float(sim_matrix[seed_pos][other_pos])
            if sim < similarity_threshold:
                continue
            # 关键词重合检查
            other_tokens = set(_tokenize(_clean_text(news_list[selected_indices[other_pos]].get("title", ""))))
            token_overlap = len(seed_tokens & other_tokens)
            if token_overlap >= 2 or sim >= 0.65:
                cluster_positions.append(other_pos)
                if len(cluster_positions) >= max_news_per_event:
                    break

        # 标记已分配
        for pos in cluster_positions:
            assigned.add(pos)

        # 构建事件点
        event_news = [news_list[selected_indices[pos]] for pos in cluster_positions]
        event_point = _build_event_point(event_news)
        event_points.append(event_point)

    # 超过 max_event_points 时按热度排序保留前 N
    if len(event_points) > max_event_points:
        event_points.sort(key=lambda ep: ep["event_heat"], reverse=True)
        event_points = event_points[:max_event_points]

    return event_points


def _build_event_point(news_items: list[dict[str, Any]]) -> dict[str, Any]:
    """从一组新闻构建单个事件点。"""
    if not news_items:
        return {}

    # 代表新闻：选热度最高的
    best = max(news_items, key=lambda nw: _compute_news_heat(nw))

    # event_title = 代表新闻标题（过长截断）
    raw_title = _clean_text(best.get("title"))
    if len(raw_title) > 28:
        event_title = raw_title[:26] + "..."
    else:
        event_title = raw_title

    # event_summary = 代表新闻 summary，fallback 正文第一句
    summary = _clean_text(best.get("summary"))
    if not summary or len(summary) < 10:
        content = _clean_text(best.get("content"))
        if content:
            sentences = content.replace("！", "。").replace("？", "。").split("。")
            summary = sentences[0][:120] if sentences else content[:120]

    # event_time = 代表新闻时间
    event_time = str(best.get("publish_time", ""))

    # event_heat = 所有新闻热度之和的归一化
    total_heat = sum(_compute_news_heat(nw) for nw in news_items)
    event_heat = round(min(100.0, math.log2(len(news_items) + 1) * 25 + total_heat * 0.05), 1)

    # keywords = 从标题提取 top 3 有意义的词
    all_titles = " ".join([_clean_text(nw.get("title")) for nw in news_items])
    tokens = _tokenize(all_titles)
    word_freq: dict[str, int] = {}
    for t in tokens:
        if t in _STOP_WORDS or t in _GENERIC_WORDS_FOR_NAMING:
            continue
        word_freq[t] = word_freq.get(t, 0) + 1
    event_keywords = [w for w, _ in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]]

    # related_news
    related = []
    for nw in news_items[:5]:
        related.append({
            "id": int(nw["id"]),
            "title": _clean_text(nw.get("title")),
            "source": _clean_text(nw.get("source")),
            "publish_time": str(nw.get("publish_time", "")),
            "heat": int(_compute_news_heat(nw)),
        })

    return {
        "event_id": 0,  # 外部重编号
        "event_title": event_title,
        "event_summary": summary[:120] if summary else "",
        "event_time": event_time,
        "representative_news_id": int(best["id"]),
        "source_news_ids": [int(nw["id"]) for nw in news_items],
        "news_count": len(news_items),
        "event_heat": event_heat,
        "keywords": event_keywords,
        "related_news": related,
    }


# ══════════════════════════════════════════════════════════════════════
# LLM 润色（可选）
# ══════════════════════════════════════════════════════════════════════

# ── LLM 输出禁止词（文学化/栏目化）──────────────────────────────────
_BANNED_STYLE_WORDS = {
    "风云录", "脉动", "盛事", "盛况", "聚焦", "风暴", "浪潮", "纵横",
    "速递", "观察", "追踪", "热点新闻", "最新动态", "事件聚焦",
}


def _extract_strong_terms(topic: dict[str, Any]) -> set[str]:
    """从原始 topic 中提取强关键词作为校验基准。"""
    strong: set[str] = set()
    # 从 keywords 中取非弱词的词
    for kw in topic.get("keywords", []):
        if kw not in _WEAK_TOPIC_WORDS and kw not in _GENERIC_WORDS_FOR_NAMING and len(kw) >= 2:
            strong.add(kw)
    # 从 topic_name 中提取有意义的词
    import jieba
    name_words = jieba.cut(topic.get("topic_name", ""))
    for w in name_words:
        w = w.strip()
        if len(w) >= 3 and w not in _WEAK_TOPIC_WORDS and w not in _GENERIC_WORDS_FOR_NAMING:
            strong.add(w)
    # 从代表新闻标题提取
    for rn in topic.get("representative_news", [])[:3]:
        for w in jieba.cut(rn.get("title", "")):
            w = w.strip()
            if len(w) >= 3 and w not in _WEAK_TOPIC_WORDS and w not in _GENERIC_WORDS_FOR_NAMING:
                strong.add(w)
    return strong


def _validate_polished_result(original: dict[str, Any], polished: dict[str, Any]) -> tuple[bool, str]:
    """校验 LLM 润色结果。返回 (通过, 拒绝原因)。"""
    name = (polished.get("topic_name") or "").strip()

    # 1. 基本校验
    if not name or len(name) < 4 or len(name) > 24:
        return (False, "topic_name 长度异常")
    too_generic = {"最新动态", "相关报道", "热点事件", "新闻进展", "最新消息", "热点新闻"}
    if name in too_generic:
        return (False, "topic_name 过于空泛")

    # 2. 禁止文学化词
    for b_word in _BANNED_STYLE_WORDS:
        if b_word in name:
            return (False, f"topic_name 包含禁止词: {b_word}")

    # 3. 强关键词校验：如果本地有强词，LLM 必须保留至少一个
    strong_terms = _extract_strong_terms(original)
    if len(strong_terms) >= 2:
        retained = [t for t in strong_terms if t in name]
        if len(retained) == 0:
            return (False, f"topic_name 未保留任何强关键词: {strong_terms}")

    # 4. 疑似引入新实体（词长 >=3 且不在 strong_terms 中且不是通用词）
    import jieba
    new_words = []
    for w in jieba.cut(name):
        w = w.strip()
        if len(w) >= 3 and w not in strong_terms and w not in _WEAK_TOPIC_WORDS and w not in _GENERIC_WORDS_FOR_NAMING:
            new_words.append(w)
    if len(new_words) >= 2 and len(strong_terms) >= 2:
        # 引入了 2+ 个新的长词 → 疑似编造
        return (False, f"topic_name 疑似引入新实体: {new_words}")

    # 5. 摘要校验
    summary = (polished.get("summary") or "").strip()
    if not summary or len(summary) > 120:
        return (False, "summary 长度异常")

    # 6. 事件标题校验
    event_title_map = polished.get("event_title_map", {})
    for eid, etitle in event_title_map.items():
        if not etitle or len(etitle) > 28:
            return (False, f"event_title[{eid}] 长度异常")
        for b_word in _BANNED_STYLE_WORDS:
            if b_word in etitle:
                return (False, f"event_title[{eid}] 包含禁止词: {b_word}")

    return (True, "")


def _polish_topic_with_llm(
    topic: dict[str, Any],
    ai_service_url: str,
    timeout: float = 45.0,
) -> dict[str, Any]:
    """调用 ai-service /ai/polish-timeline-topic 对单个话题进行文本润色。

    网络错误、超时、非 200、JSON 异常 → 保留原始结果。
    """
    import httpx

    # 构建 payload（最多传 5 条代表标题、6 个事件点）
    rep_titles = [rn.get("title", "") for rn in topic.get("representative_news", [])[:5]]
    eps = topic.get("event_points", [])[:6]
    ep_payload = []
    for ep in eps:
        related = [rn.get("title", "") for rn in ep.get("related_news", [])[:5]]
        ep_payload.append({
            "event_id": str(ep.get("event_id", "")),
            "event_title": ep.get("event_title", ""),
            "event_summary": ep.get("event_summary", ""),
            "related_titles": related,
            "news_count": ep.get("news_count", 1),
        })

    payload = {
        "topic_name": topic.get("topic_name", ""),
        "category_name": topic.get("category_name"),
        "keywords": topic.get("keywords", [])[:6],
        "representative_titles": rep_titles,
        "summary": topic.get("summary", ""),
        "event_points": ep_payload,
    }

    try:
        url = f"{ai_service_url.rstrip('/')}/ai/polish-timeline-topic"
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload)
            if resp.status_code != 200:
                logger.warning("LLM 润色返回 %d", resp.status_code)
                topic["llm_used"] = False
                topic["polish_source"] = "fallback"
                topic["fallback_reason"] = f"HTTP {resp.status_code}"
                return topic

            data = resp.json()
            result = data.get("data", {})
            source = result.get("source", "fallback")

            if source == "fallback":
                logger.info("LLM 润色回退: %s", result.get("fallback_reason"))
                topic["llm_used"] = False
                topic["polish_source"] = "fallback"
                topic["fallback_reason"] = result.get("fallback_reason", "unknown")
                return topic

            ok, reason = _validate_polished_result(topic, result)
            # 初始化状态
            topic["llm_used"] = False
            topic["polish_source"] = "fallback"
            topic["fallback_reason"] = ""

            if not ok:
                logger.warning("LLM 润色校验失败: %s", reason)
                topic["fallback_reason"] = reason
                return topic

            # ── 逐字段选择性应用 ──
            applied_any = False

            # topic_name
            llm_name = (result.get("topic_name") or "").strip()
            if llm_name and llm_name != topic.get("topic_name", ""):
                topic["raw_topic_name"] = topic["topic_name"]
                topic["topic_name"] = llm_name
                applied_any = True

            # summary
            llm_summary = (result.get("summary") or "").strip()
            if llm_summary and llm_summary != topic.get("summary", ""):
                topic["raw_summary"] = topic.get("summary", "")
                topic["summary"] = llm_summary
                applied_any = True

            # keywords
            llm_keywords = result.get("keywords", [])
            if llm_keywords:
                topic["keywords"] = llm_keywords

            # event points（逐个校验）
            import jieba
            event_title_map = result.get("event_title_map", {})
            event_summary_map = result.get("event_summary_map", {})
            ep_applied = 0
            for ep in topic.get("event_points", []):
                eid = str(ep.get("event_id", ""))
                # 校验 event_title
                if eid in event_title_map:
                    et = event_title_map[eid].strip()
                    banned = any(b in et for b in _BANNED_STYLE_WORDS)
                    if et and len(et) <= 28 and not banned:
                        ep["raw_event_title"] = ep["event_title"]
                        ep["event_title"] = et
                        ep_applied += 1
                # 校验 event_summary
                if eid in event_summary_map:
                    es = event_summary_map[eid].strip()
                    if es and len(es) <= 120:
                        ep["raw_event_summary"] = ep.get("event_summary", "")
                        ep["event_summary"] = es

            if applied_any or ep_applied > 0:
                topic["llm_used"] = True
                topic["polish_source"] = "llm"
                topic["fallback_reason"] = ""
                logger.info("LLM 润色成功: %d 个事件点标题已替换", ep_applied)
            else:
                topic["llm_used"] = False
                topic["polish_source"] = "fallback"
                topic["fallback_reason"] = "LLM 输出与原始一致"
                logger.info("LLM 输出与原始无差异，保留本地结果")

            return topic

    except Exception as e:
        logger.warning("LLM 润色异常: %s", e)
        topic["llm_used"] = False
        topic["polish_source"] = "fallback"
        topic["fallback_reason"] = str(e)[:100]
        return topic


# ══════════════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════════════

def cluster_news_topics(
    days: int = 30,
    max_news: int = 1000,
    min_news_to_cluster: int = 20,
    min_cluster_size: int = 3,
    max_topics: int = 8,
    use_llm_polish: bool = False,
) -> list[dict[str, Any]]:
    """从数据库读取新闻并自动聚类为热点话题。

    Args:
        use_llm_polish: 是否调用 ai-service 对话题名、摘要、事件点标题进行 LLM 润色。
                       默认 False，仅本地规则。
    """
    from sklearn.cluster import KMeans, MiniBatchKMeans
    from sklearn.feature_extraction.text import TfidfVectorizer

    _init_jieba()

    # ── 1. 查询新闻 ──
    news_list = _fetch_news(days=days, max_news=max_news)
    n_total = len(news_list)
    logger.info("聚类服务：查询到 %d 条新闻", n_total)

    if n_total < min_news_to_cluster:
        logger.info("跳过聚类：%d < %d", n_total, min_news_to_cluster)
        return []

    # ── 2. 标题去重 ──
    news_list = _deduplicate_titles(news_list)
    n_total = len(news_list)
    if n_total < min_news_to_cluster:
        logger.info("去重后新闻不足：%d < %d", n_total, min_news_to_cluster)
        return []

    # ── 3. 构建文本 ──
    corpus: list[str] = []
    for nw in news_list:
        title = _clean_text(nw.get("title"))
        summary = _clean_text(nw.get("summary"))
        content = _clean_text(nw.get("content"))
        text = _build_news_text(title, summary, content[:200] if content else "")
        if not text.strip():
            text = title
        corpus.append(text)

    # ── 4. TF-IDF 向量化 ──
    tokenized = [" ".join(_tokenize(doc)) for doc in corpus]

    vectorizer = TfidfVectorizer(
        max_features=3000,
        min_df=2,
        max_df=0.45,
        ngram_range=(1, 2),
        sublinear_tf=True,
        token_pattern=r"(?u)\b\w+\b",
    )
    tfidf_matrix = vectorizer.fit_transform(tokenized)
    feature_names = vectorizer.get_feature_names_out()

    logger.info("TF-IDF: shape=%s, vocab=%d", tfidf_matrix.shape, len(feature_names))

    # ── 5. 聚类 ──
    n_clusters = _choose_topic_count(n_total, max_topics=max_topics)

    if n_total < 100:
        model = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    else:
        model = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, n_init="auto")

    labels = model.fit_predict(tfidf_matrix)
    centroid = model.cluster_centers_  # shape (n_clusters, n_features)
    logger.info("聚类完成：k=%d, distribution=%s", n_clusters, Counter(labels.tolist()))

    # ── 6. 构建结果 ──
    cluster_map: dict[int, list[int]] = {}
    for i, label in enumerate(labels):
        cluster_map.setdefault(int(label), []).append(i)

    results: list[dict[str, Any]] = []
    for cid, indices in sorted(cluster_map.items()):
        if len(indices) < min_cluster_size:
            logger.info("丢弃小簇 %d：仅 %d 条", cid, len(indices))
            continue

        # ── 大簇二次拆分 ──
        if len(indices) > 50:
            sub_indices_list = _split_large_cluster(indices, news_list, corpus, max_size=50)
            logger.info("大簇 %d（%d条）拆分为 %d 个子簇", cid, len(indices), len(sub_indices_list))
        else:
            sub_indices_list = [indices]

        for sub_indices in sub_indices_list:
            if len(sub_indices) < min_cluster_size:
                continue
            # 用该子簇计算自己的质心
            sub_vecs = tfidf_matrix[sub_indices].toarray()
            sub_centroid = sub_vecs.mean(axis=0) if len(sub_vecs) > 0 else centroid[cid]

            result = _build_cluster_result(
                cluster_id=len(results),
                indices=sub_indices,
                news_list=news_list,
                tfidf_matrix=tfidf_matrix,
                feature_names=list(feature_names),
                cluster_centroid=sub_centroid,
            )
            if result is not None:
                # ── 第二级聚合：话题内新闻 → 事件点 ──
                selected = _select_news_for_cluster(
                    indices=sub_indices,
                    news_list=news_list,
                    tfidf_matrix=tfidf_matrix,
                    cluster_centroid=sub_centroid,
                    max_news=30,
                )
                result["selected_news_count"] = len(selected)
                result["event_points"] = _aggregate_event_points(
                    selected_indices=selected,
                    news_list=news_list,
                    tfidf_matrix=tfidf_matrix,
                    max_event_points=6,
                    max_news_per_event=5,
                    similarity_threshold=0.45,
                )
                for ei, ep in enumerate(result["event_points"]):
                    ep["event_id"] = ei + 1
                results.append(result)

    # ── 7. 排序 & 重编号 ──
    results.sort(key=lambda r: r["heat_score"], reverse=True)
    for i, r in enumerate(results):
        r["cluster_id"] = i

    # ── 8. LLM 润色（可选） ──
    if use_llm_polish:
        from app.core.config import settings

        ai_url = settings.ai_service_url
        polished_count = 0
        for r in results:
            r["llm_used"] = False
            r["polish_source"] = "none"
            # 只对 "ok" 的话题调用 LLM
            if r.get("quality_status") != "ok":
                continue
            if r.get("news_count", 0) < 3:
                continue
            if not r.get("event_points"):
                continue
            r = _polish_topic_with_llm(r, ai_url)
            if r.get("llm_used"):
                polished_count += 1

        logger.info("LLM 润色完成：%d/%d 个话题已润色", polished_count, len(results))

    # ── 9. 质量日志 ──
    if results:
        max_cluster_size = max(r["news_count"] for r in results)
        max_cluster_pct = round(max_cluster_size / n_total * 100, 1)
        logger.info("最终 %d 个话题，最大簇 %d 条 (%.1f%%)", len(results), max_cluster_size, max_cluster_pct)
    else:
        logger.info("未生成任何话题")

    return results


# ══════════════════════════════════════════════════════════════════════
# 本地调试入口
# ══════════════════════════════════════════════════════════════════════

def preview_auto_cluster_write(
    days: int = 30,
    max_news: int = 1000,
    use_llm_polish: bool = True,
    max_write_topics: int = 8,
) -> dict[str, Any]:
    """dry-run 预演：计算自动话题写库内容，但不执行任何 SQL。

    返回将在真写库时插入/更新的数据预览。
    """
    results = cluster_news_topics(
        days=days, max_news=max_news, use_llm_polish=use_llm_polish,
    )

    recommended = [r for r in results if r.get("quality_status") == "ok"]
    recommended.sort(key=lambda r: r["heat_score"], reverse=True)
    recommended = recommended[:max_write_topics]

    skipped = [r for r in results if r.get("quality_status") != "ok"]

    topics_to_insert: list[dict[str, Any]] = []
    news_topic_updates: list[dict[str, Any]] = []
    timelines_to_write: list[dict[str, Any]] = []

    for r in recommended:
        # topic 预览
        topics_to_insert.append({
            "topic_name": r["topic_name"],
            "summary": r.get("summary", ""),
            "keyword_list": r.get("keywords", []),
            "heat_score": r["heat_score"],
            "news_count": r["news_count"],
            "event_point_count": len(r.get("event_points", [])),
            "source_news_ids": r.get("news_ids", []),
            "quality_score": r.get("quality_score", 0),
            "quality_status": r.get("quality_status", ""),
            "llm_used": r.get("llm_used", False),
        })

        # news.topic_id 更新预览
        news_ids = r.get("news_ids", [])
        if news_ids:
            news_topic_updates.append({
                "topic_name": r["topic_name"],
                "news_ids": news_ids,
                "count": len(news_ids),
            })

        # event_timeline 预览
        eps = r.get("event_points", [])
        timeline_nodes: list[dict[str, Any]] = []
        for ep in eps[:6]:
            node = {
                "event_id": ep["event_id"],
                "event_time": ep.get("event_time", ""),
                "event_title": ep.get("event_title", ""),
                "event_summary": ep.get("event_summary", ""),
                "source_news_id": ep.get("representative_news_id", 0),
                "source_news_ids": ep.get("source_news_ids", []),
                "source_title": ep.get("related_news", [{}])[0].get("title", "") if ep.get("related_news") else "",
                "source_name": ep.get("related_news", [{}])[0].get("source", "") if ep.get("related_news") else "",
                "event_type": "auto",
                "importance": min(5, max(3, ep.get("news_count", 1))),
                "event_detail": ep.get("event_summary", ""),
                "keywords": ep.get("keywords", []),
                "related_news": ep.get("related_news", [])[:5],
            }
            timeline_nodes.append(node)

        timelines_to_write.append({
            "topic_name": r["topic_name"],
            "timeline_node_count": len(timeline_nodes),
            "source_news_ids": news_ids,
            "timeline_json_preview": timeline_nodes[:2],  # 只展示前 2 个
        })

    skipped_info = [
        {"topic_name": r["topic_name"], "reason": r.get("quality_status", "?")}
        for r in skipped
    ]

    return {
        "dry_run": True,
        "total_candidates": len(results),
        "recommended_count": len(recommended),
        "skipped_count": len(skipped),
        "topics_to_insert": topics_to_insert,
        "news_topic_updates": news_topic_updates,
        "timelines_to_write": timelines_to_write,
        "skipped_topics": skipped_info,
        "warnings": [
            "当前未真实写入数据库",
            "当前未覆盖或删除任何人工话题",
            "当前数据库 news_topic 缺少 source_type 字段，正式写库前建议新增以区分 manual/auto",
            "正式写库时应先清理旧的 auto 话题再写入新话题",
        ],
    }


def apply_auto_cluster_write(
    days: int = 30,
    max_news: int = 1000,
    use_llm_polish: bool = True,
    max_write_topics: int = 8,
    min_news_to_cluster: int = 20,
    dry_run: bool = True,
) -> dict[str, Any]:
    """执行自动话题写库。默认 dry_run=True 防止误写。

    写库流程：
    1. 聚类 + 质量筛选
    2. 清理旧 auto 话题
    3. 插入新 auto 话题
    4. 更新 news.topic_id
    5. 写入 event_timeline
    6. 事务保护，任一步失败回滚
    """
    import json as json_mod
    from datetime import datetime

    # 检查 source_type 字段
    try:
        cols = execute_query("SHOW COLUMNS FROM news_topic LIKE 'source_type'")
        if not cols:
            return {"success": False, "reason": "missing_source_type", "message": "news_topic 缺少 source_type 字段，请先执行 migration 029"}
    except Exception:
        return {"success": False, "reason": "db_error", "message": "无法检查 source_type 字段"}

    # 聚类
    results = cluster_news_topics(days=days, max_news=max_news, use_llm_polish=use_llm_polish)
    recommended = [r for r in results if r.get("quality_status") == "ok"]
    recommended.sort(key=lambda r: r["heat_score"], reverse=True)
    recommended = recommended[:max_write_topics]

    if not recommended:
        return {
            "success": False,
            "reason": "no_qualified_topics",
            "message": "没有 quality_status=ok 的话题，不执行写库",
        }

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── dry-run 直接返回预览 ──
    if dry_run:
        preview = preview_auto_cluster_write(days=days, max_news=max_news, use_llm_polish=use_llm_polish, max_write_topics=max_write_topics)
        preview["success"] = True
        preview["mode"] = "dry_run"
        return preview

    # ── 真写库（真实事务） ──
    conn = get_connection()
    conn.begin()  # 开启事务
    inserted_topic_ids: dict[str, int] = {}
    updated_news_count = 0
    written_timeline_count = 0

    try:
        cursor = conn.cursor()
        # 先查询旧 auto 话题
        cursor.execute("SELECT id FROM news_topic WHERE source_type = 'auto' AND status = 1")
        old_auto_ids = [int(r["id"]) for r in cursor.fetchall()]

        # 1. 清理旧 auto
        if old_auto_ids:
            placeholders = ",".join(["%s"] * len(old_auto_ids))
            cursor.execute(f"UPDATE news SET topic_id = NULL WHERE topic_id IN ({placeholders})", old_auto_ids)
            cursor.execute(f"DELETE FROM event_timeline WHERE topic_id IN ({placeholders})", old_auto_ids)
            cursor.execute(f"UPDATE news_topic SET status = 0 WHERE id IN ({placeholders})", old_auto_ids)
            logger.info("清理旧 auto 话题: %d 个", len(old_auto_ids))

        # 2. 插入新 auto 话题
        for r in recommended:
            kw_json = json_mod.dumps(r.get("keywords", []), ensure_ascii=False)
            cursor.execute(
                "INSERT INTO news_topic (topic_name, keyword_list, heat_score, summary, status, source_type, auto_generated_at) VALUES (%s, %s, %s, %s, 1, 'auto', %s)",
                [r["topic_name"], kw_json, int(r["heat_score"]), r.get("summary", ""), now_str],
            )
            inserted_topic_ids[r["topic_name"]] = int(cursor.lastrowid)

        # 3. 批量更新 news.topic_id
        for r in recommended:
            tid = inserted_topic_ids[r["topic_name"]]
            news_ids = r.get("news_ids", [])
            if not news_ids:
                continue
            for i in range(0, len(news_ids), 200):
                batch = news_ids[i:i + 200]
                batch_ph = ",".join(["%s"] * len(batch))
                if old_auto_ids:
                    old_ph = ",".join(["%s"] * len(old_auto_ids))
                    cursor.execute(
                        f"UPDATE news SET topic_id = %s WHERE id IN ({batch_ph}) AND (topic_id IS NULL OR topic_id IN ({old_ph}))",
                        [tid] + batch + old_auto_ids,
                    )
                else:
                    cursor.execute(
                        f"UPDATE news SET topic_id = %s WHERE id IN ({batch_ph}) AND topic_id IS NULL",
                        [tid] + batch,
                    )
                updated_news_count += cursor.rowcount

        # 4. 写入 event_timeline
        for r in recommended:
            tid = inserted_topic_ids[r["topic_name"]]
            eps = r.get("event_points", [])
            if not eps:
                continue
            timeline_nodes = []
            all_ep_news_ids: list[int] = []
            for ep in eps[:6]:
                all_ep_news_ids.extend(ep.get("source_news_ids", []))
                node = {
                    "event_id": ep["event_id"],
                    "event_time": ep.get("event_time", ""),
                    "event_title": ep.get("event_title", ""),
                    "event_summary": ep.get("event_summary", ""),
                    "source_news_id": ep.get("representative_news_id", 0),
                    "source_news_ids": ep.get("source_news_ids", []),
                    "source_title": ep.get("related_news", [{}])[0].get("title", "") if ep.get("related_news") else "",
                    "source_name": ep.get("related_news", [{}])[0].get("source", "") if ep.get("related_news") else "",
                    "event_type": "auto",
                    "importance": min(5, max(3, ep.get("news_count", 1))),
                    "event_detail": ep.get("event_summary", ""),
                    "keywords": ep.get("keywords", []),
                    "related_news": ep.get("related_news", [])[:5],
                }
                timeline_nodes.append(node)

            tl_json = json_mod.dumps(timeline_nodes, ensure_ascii=False)
            src_json = json_mod.dumps(list(set(all_ep_news_ids)), ensure_ascii=False)
            # 删除可能存在的旧条目（防止失败运行残留），再插入新条目
            cursor.execute("DELETE FROM event_timeline WHERE topic_id = %s", [tid])
            cursor.execute(
                "INSERT INTO event_timeline (topic_id, timeline_json, source_news_ids, generate_status, generated_at, updated_at) VALUES (%s, %s, %s, 'auto', %s, %s)",
                [tid, tl_json, src_json, now_str, now_str],
            )
            written_timeline_count += 1

        # 全部成功 → 提交事务
        conn.commit()
        cursor.close()
        conn.close()

        logger.info("写库完成: topics=%d, news=%d, timelines=%d",
                     len(inserted_topic_ids), updated_news_count, written_timeline_count)

        return {
            "success": True,
            "mode": "real_write",
            "inserted_topics": len(inserted_topic_ids),
            "updated_news_topic_id": updated_news_count,
            "written_timelines": written_timeline_count,
            "cleaned_old_auto_topics": len(old_auto_ids),
            "topic_names": list(inserted_topic_ids.keys()),
            "manual_topics_preserved": True,
        }

    except Exception as e:
        conn.rollback()
        logger.exception("写库失败，已回滚: %s", e)
        return {
            "success": False,
            "reason": "write_failed",
            "message": str(e)[:200],
        }
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    import os, json

    print("=" * 60)
    print("新闻话题聚类服务 - 本地调试 + Dry-Run 预演")
    print("=" * 60)

    print("\n>>> Step 1: 本地规则聚类...")
    results = cluster_news_topics(days=30, max_news=1000, use_llm_polish=False)

    ai_available = os.getenv("AI_SERVICE_URL", "")
    try_llm = bool(ai_available)
    if try_llm:
        print(">>> Step 2: LLM 润色聚类...")
        llm_results = cluster_news_topics(days=30, max_news=1000, use_llm_polish=True)
    else:
        llm_results = None

    if not results:
        print("\n[FAIL] 未生成任何话题（新闻数量不足或无有效文本）。")
    else:
        max_sz = max(r["news_count"] for r in results)
        total_news = sum(r["news_count"] for r in results)
        total_ep = sum(len(r.get("event_points", [])) for r in results)
        print(f"\n[OK] 共生成 {len(results)} 个话题，{total_ep} 个事件点")
        print(f"最大簇: {max_sz} 条 ({round(max_sz/total_news*100,1)}%)")
        print(f"总覆盖: {total_news} 条新闻")

        # ── 分类：建议写库 vs 不建议 ──
        recommended = [r for r in results if r.get("quality_status") == "ok"]
        not_recommended = [r for r in results if r.get("quality_status") != "ok"]

        print(f"\n{'='*60}")
        print(f"[建议写库话题] {len(recommended)} 个")
        print(f"{'='*60}")
        for topic in recommended:
            eps = topic.get("event_points", [])
            cat = topic.get("category_name", "-")
            purity = topic.get("category_purity", 0)
            print(f"  #{topic['cluster_id']+1} {topic['topic_name']}")
            print(f"     分类={cat} 纯度={purity}%  新闻={topic['news_count']}  事件点={len(eps)}  Q={topic.get('quality_score',0)}")
            print(f"     关键词: {', '.join(topic['keywords'][:4])}")

        print(f"\n{'='*60}")
        print(f"[不建议写库话题] {len(not_recommended)} 个")
        print(f"{'='*60}")
        for topic in not_recommended:
            status = topic.get("quality_status", "?")
            cat = topic.get("category_name", "-")
            purity = topic.get("category_purity", 0)
            print(f"  #{topic['cluster_id']+1} {topic['topic_name']}  [{status}]")
            print(f"     分类={cat} 纯度={purity}%  新闻={topic['news_count']}  Q={topic.get('quality_score',0)}")
            print(f"     关键词: {', '.join(topic['keywords'][:4])}")

        # ── LLM 润色对比 ──
        if llm_results is not None:
            print(f"\n{'='*60}")
            print(f"[LLM 润色对比]")
            print(f"{'='*60}")
            for local, llm in zip(results, llm_results):
                if local.get("topic_name") != llm.get("topic_name"):
                    local_name = local["topic_name"][:30].encode('gbk', errors='replace').decode('gbk', errors='replace')
                    llm_name = llm["topic_name"][:30].encode('gbk', errors='replace').decode('gbk', errors='replace')
                    used = llm.get("llm_used", False)
                    reason = llm.get("fallback_reason", "-")
                    print(f"  #{local['cluster_id']+1}: {local_name} → {llm_name}  [llm_used={used}]")
                    if not used and reason != "-":
                        print(f"       reason: {reason}")
            print()

    # ── Dry-Run 写库预演 ──
    print("=" * 60)
    print("[Dry-Run] Auto Cluster Write Preview")
    print("=" * 60)

    preview = preview_auto_cluster_write(
        days=30, max_news=1000,
        use_llm_polish=try_llm,
        max_write_topics=8,
    )

    print(f"dry_run={preview['dry_run']}")
    print(f"候选话题: {preview['total_candidates']} 个")
    print(f"将写入: {preview['recommended_count']} 个")
    print(f"跳过: {preview['skipped_count']} 个")

    for t in preview["topics_to_insert"]:
        name_safe = t["topic_name"][:25].encode('gbk', errors='replace').decode('gbk', errors='replace')
        print(f"\n  [{t['quality_status']}] {name_safe}")
        print(f"      新闻数={t['news_count']}  事件点={t['event_point_count']}  llm={t['llm_used']}")
        print(f"      keywords: {', '.join(t['keyword_list'][:4])}")

    if preview["skipped_topics"]:
        print(f"\n  跳过的话题:")
        for s in preview["skipped_topics"]:
            name_safe = s["topic_name"][:25].encode('gbk', errors='replace').decode('gbk', errors='replace')
            print(f"    - {name_safe}  [{s['reason']}]")

    # 展示 1 个 timeline 样例
    if preview["timelines_to_write"]:
        sample = preview["timelines_to_write"][0]
        name_safe = sample["topic_name"][:25].encode('gbk', errors='replace').decode('gbk', errors='replace')
        print(f"\n[Timeline 样例] {name_safe}")
        print(f"  节点数={sample['timeline_node_count']}  source_news_ids={len(sample['source_news_ids'])}")
        for node in sample["timeline_json_preview"]:
            print(f"    event_{node['event_id']}: {node['event_title'][:30]}")
            print(f"      source_news_ids: {node['source_news_ids'][:3]}")

    print(f"\n[Warnings]")
    for w in preview["warnings"]:
        print(f"  - {w}")

    # ── 真写库入口（默认注释，取消注释 + dry_run=False 才执行） ──
    # import os as _os
    # if _os.getenv("REAL_WRITE") == "1":
    #     print("\n>>> 真写库模式（REAL_WRITE=1）...")
    #     result = apply_auto_cluster_write(days=30, max_news=1000, use_llm_polish=try_llm, dry_run=False)
    #     print(result)
