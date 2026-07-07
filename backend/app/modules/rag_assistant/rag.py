"""RAG 多资源检索器 — 新闻 / 帖子 / 评论 / 话题"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.db.database import execute_query
from app.modules.rag_assistant.schema import SearchResultItem

logger = logging.getLogger(__name__)

CONTENT_TRUNCATE = 2000
MAX_RESULTS = 8


class MultiResourceRetriever:
    """多资源检索器"""

    # ══════════════════════════════════════════════════════
    # 公共入口
    # ══════════════════════════════════════════════════════

    async def retrieve(
        self, question: str, context: Dict[str, Any], max_results: int = MAX_RESULTS
    ) -> Dict[str, Any]:
        # ── 日志：收到检索请求 ──
        logger.info(
            "[RAG] ═══ 收到检索请求 ═══\n"
            "  问题: %s\n"
            "  上下文: page=%s newsId=%s postId=%s topicId=%s categoryId=%s keyword=%s",
            question,
            context.get("page"), context.get("newsId"), context.get("postId"),
            context.get("topicId"), context.get("categoryId"), context.get("searchKeyword"),
        )

        try:
            results: List[SearchResultItem] = []
            exclude: Dict[str, set] = {}  # {"news": {1,2}, "post": {...}}

            # ── Step 0: 当前资源 ──
            current = self._get_current_resource(context)
            if current:
                logger.info("[RAG] Step0 当前资源: type=%s id=%s title=%s", current.type, current.id, current.title)
                self._add_exclude(exclude, current)
            else:
                logger.info("[RAG] Step0 当前资源: 无")
        except Exception as e:
            logger.warning("[RAG] Step0 失败: %s", e)
            current = None
            exclude = {}

        try:
            # ── Step 1: 关联检索 ──
            if current:
                related = self._get_related(current, exclude, max_results)
                for r in related:
                    self._add_exclude(exclude, r)
                results.extend(related)
                logger.info("[RAG] Step1 关联检索: %d 条", len(related))
        except Exception as e:
            logger.warning("[RAG] Step1 失败: %s", e)

        try:
            # ── Step 2: 全文搜索补足 ──
            remain = max_results - len(results)
            if remain > 0:
                searched = self._fulltext_multi_search(question, exclude, remain)
                results.extend(searched)
                logger.info("[RAG] Step2 全文搜索: %d 条", len(searched))
        except Exception as e:
            logger.warning("[RAG] Step2 失败: %s", e)

        # ── 日志：汇总检索结果 ──
        final = results[:max_results]
        logger.info(
            "[RAG] ═══ 检索完成 ═══ 当前资源:%s 关联:%d 总计:%d 条",
            current.type if current else "无",
            len(results) - len(final) + len(results) if current else 0,  # rough
            len(final) + (1 if current else 0),
        )
        for i, r in enumerate(final):
            logger.info(
                "[RAG]   结果%d: type=%s id=%s relevance=%s title=%s",
                i + 1, r.type, r.id, r.relevance, (r.title or (r.content or '')[:40]),
            )

        return {
            "current": _item_to_dict(current),
            "articles": [_item_to_dict(r) for r in final],
        }

    # ══════════════════════════════════════════════════════
    # Step 0: 当前资源
    # ══════════════════════════════════════════════════════

    def _get_current_resource(self, ctx: Dict[str, Any]) -> Optional[SearchResultItem]:
        page = ctx.get("page", "other")

        if page == "news-detail" and ctx.get("newsId"):
            return self._get_news_by_id(ctx["newsId"], relevance="current")

        if page == "community" and ctx.get("postId"):
            return self._get_post_by_id(ctx["postId"], relevance="current")

        if page == "timeline" and ctx.get("topicId"):
            return self._get_topic_by_id(ctx["topicId"], relevance="current")

        if page == "home":
            keyword = ctx.get("searchKeyword")
            if keyword:
                return SearchResultItem(
                    type="news_topic",
                    id=0,
                    title=f"搜索: {keyword}",
                    content=f"用户正在首页搜索关键词「{keyword}」",
                    relevance="current",
                )
            cat_id = ctx.get("categoryId")
            if cat_id:
                cat = self._get_category(cat_id)
                if cat:
                    return SearchResultItem(
                        type="news_topic",
                        id=0,
                        title=f"新闻分类: {cat.get('name', '')}",
                        content=f"用户正在浏览「{cat.get('name', '')}」分类下的新闻",
                        relevance="current",
                    )

        return None

    # ══════════════════════════════════════════════════════
    # Step 1: 关联检索
    # ══════════════════════════════════════════════════════

    def _get_related(
        self, current: SearchResultItem, exclude: Dict[str, set], max_results: int
    ) -> List[SearchResultItem]:
        results: List[SearchResultItem] = []

        if current.type == "news":
            # 同话题新闻
            if current.topicId:
                results.extend(
                    self._search_news_by_topic(current.topicId, exclude.get("news", set()), 3)
                )
            # 关联帖子
            results.extend(self._search_posts_by_news(current.id, 2))
            # 该新闻的热门评论
            results.extend(self._search_news_comments(current.id, 2))

        elif current.type == "community_post":
            # 帖子关联的新闻
            if current.newsId:
                linked = self._get_news_by_id(current.newsId, relevance="topic_match")
                if linked:
                    results.append(linked)
            # 同话题帖子
            if current.topicId:
                results.extend(
                    self._search_posts_by_topic(current.topicId, exclude.get("community_post", set()), 3)
                )
            # 该帖子下的评论
            results.extend(self._search_post_comments(current.id, 3))

        elif current.type == "news_topic":
            results.extend(self._search_news_by_topic(current.id, exclude.get("news", set()), 4))
            results.extend(self._search_posts_by_topic(current.id, exclude.get("community_post", set()), 2))

        return results[:max_results]

    # ══════════════════════════════════════════════════════
    # 单资源查询
    # ══════════════════════════════════════════════════════

    def _get_news_by_id(self, news_id: int, relevance: str = "current") -> Optional[SearchResultItem]:
        rows = execute_query(
            "SELECT id, title, summary, content, source, publish_time, topic_id, category_id "
            "FROM news WHERE id = %s AND status = 1",
            [news_id],
        )
        if not rows:
            return None
        r = rows[0]
        content = (r.get("content") or "")[:CONTENT_TRUNCATE]
        return SearchResultItem(
            type="news",
            id=r["id"],
            title=r.get("title"),
            summary=r.get("summary"),
            content=content,
            source=r.get("source"),
            publishTime=_iso(r.get("publish_time")),
            topicId=r.get("topic_id"),
            categoryId=r.get("category_id"),
            relevance=relevance,
        )

    def _get_post_by_id(self, post_id: int, relevance: str = "current") -> Optional[SearchResultItem]:
        rows = execute_query(
            "SELECT p.id, p.title, p.content, p.user_id, p.related_news_id, p.topic_id, "
            "p.created_at, u.nickname "
            "FROM community_post p LEFT JOIN user u ON p.user_id = u.id "
            "WHERE p.id = %s AND p.status = 1",
            [post_id],
        )
        if not rows:
            return None
        r = rows[0]
        content = (r.get("content") or "")[:CONTENT_TRUNCATE]
        return SearchResultItem(
            type="community_post",
            id=r["id"],
            title=r.get("title"),
            content=content,
            source=r.get("nickname"),
            publishTime=_iso(r.get("created_at")),
            newsId=r.get("related_news_id"),
            topicId=r.get("topic_id"),
            relevance=relevance,
        )

    def _get_topic_by_id(self, topic_id: int, relevance: str = "current") -> Optional[SearchResultItem]:
        rows = execute_query(
            "SELECT id, topic_name, summary, keyword_list FROM news_topic WHERE id = %s AND status = 1",
            [topic_id],
        )
        if not rows:
            return None
        r = rows[0]
        content = r.get("summary") or ""
        return SearchResultItem(
            type="news_topic",
            id=r["id"],
            title=r.get("topic_name"),
            content=content,
            relevance=relevance,
        )

    def _get_category(self, cat_id: int) -> Optional[Dict[str, Any]]:
        rows = execute_query(
            "SELECT name FROM news_category WHERE id = %s",
            [cat_id],
        )
        return rows[0] if rows else None

    # ══════════════════════════════════════════════════════
    # 关联查询
    # ══════════════════════════════════════════════════════

    def _search_news_by_topic(
        self, topic_id: int, exclude_ids: set, limit: int
    ) -> List[SearchResultItem]:
        if not topic_id:
            return []
        exclude = exclude_ids | {0}
        placeholders = ",".join(["%s"] * len(exclude))
        rows = execute_query(
            f"SELECT id, title, summary, SUBSTRING(content, 1, %s) AS content, "
            f"source, publish_time, topic_id, category_id "
            f"FROM news WHERE topic_id = %s AND id NOT IN ({placeholders}) AND status = 1 "
            f"ORDER BY publish_time DESC LIMIT %s",
            [CONTENT_TRUNCATE, topic_id] + list(exclude) + [limit],
        )
        return [_row_to_news(r, "topic_match") for r in (rows or [])]

    def _search_posts_by_news(self, news_id: int, limit: int) -> List[SearchResultItem]:
        rows = execute_query(
            "SELECT p.id, p.title, SUBSTRING(p.content, 1, %s) AS content, "
            "u.nickname, p.created_at, p.topic_id, p.related_news_id "
            "FROM community_post p LEFT JOIN user u ON p.user_id = u.id "
            "WHERE p.related_news_id = %s AND p.status = 1 "
            "ORDER BY p.heat_score DESC LIMIT %s",
            [CONTENT_TRUNCATE, news_id, limit],
        )
        return [_row_to_post(r, "topic_match") for r in (rows or [])]

    def _search_posts_by_topic(
        self, topic_id: int, exclude_ids: set, limit: int
    ) -> List[SearchResultItem]:
        if not topic_id:
            return []
        exclude = exclude_ids | {0}
        placeholders = ",".join(["%s"] * len(exclude))
        rows = execute_query(
            f"SELECT p.id, p.title, SUBSTRING(p.content, 1, %s) AS content, "
            f"u.nickname, p.created_at, p.topic_id, p.related_news_id "
            f"FROM community_post p LEFT JOIN user u ON p.user_id = u.id "
            f"WHERE p.topic_id = %s AND p.id NOT IN ({placeholders}) AND p.status = 1 "
            f"ORDER BY p.heat_score DESC LIMIT %s",
            [CONTENT_TRUNCATE, topic_id] + list(exclude) + [limit],
        )
        return [_row_to_post(r, "topic_match") for r in (rows or [])]

    def _search_news_comments(self, news_id: int, limit: int) -> List[SearchResultItem]:
        rows = execute_query(
            "SELECT id, content, user_id, created_at "
            "FROM news_comment WHERE news_id = %s AND parent_id IS NULL AND status = 1 "
            "ORDER BY like_count DESC LIMIT %s",
            [news_id, limit],
        )
        return [
            SearchResultItem(
                type="news_comment",
                id=r["id"],
                content=(r.get("content") or "")[:CONTENT_TRUNCATE],
                source=f"用户{r.get('user_id')}",
                publishTime=_iso(r.get("created_at")),
                newsId=news_id,
                relevance="topic_match",
            )
            for r in (rows or [])
        ]

    def _search_post_comments(self, post_id: int, limit: int) -> List[SearchResultItem]:
        rows = execute_query(
            "SELECT id, content, user_id, created_at "
            "FROM post_comment WHERE post_id = %s AND parent_id IS NULL AND status = 1 "
            "ORDER BY like_count DESC LIMIT %s",
            [post_id, limit],
        )
        return [
            SearchResultItem(
                type="post_comment",
                id=r["id"],
                content=(r.get("content") or "")[:CONTENT_TRUNCATE],
                source=f"用户{r.get('user_id')}",
                publishTime=_iso(r.get("created_at")),
                postId=post_id,
                relevance="topic_match",
            )
            for r in (rows or [])
        ]

    # ══════════════════════════════════════════════════════
    # Step 2: 全文搜索
    # ══════════════════════════════════════════════════════

    def _fulltext_multi_search(
        self, question: str, exclude: Dict[str, set], limit: int
    ) -> List[SearchResultItem]:
        results: List[SearchResultItem] = []

        # 搜索新闻
        news_results = self._fulltext_search_news(question, exclude.get("news", set()), limit)
        results.extend(news_results)

        # 搜索帖子
        remain = limit - len(results)
        if remain > 0:
            post_results = self._fulltext_search_posts(question, exclude.get("community_post", set()), remain)
            results.extend(post_results)

        return results

    def _fulltext_search_news(
        self, question: str, exclude_ids: set, limit: int
    ) -> List[SearchResultItem]:
        # 对问题做简单的分词处理，构造 BOOLEAN MODE 查询
        keywords = _tokenize_for_fulltext(question)
        if not keywords:
            return []

        exclude = exclude_ids | {0}
        placeholders = ",".join(["%s"] * len(exclude))
        sql = (
            f"SELECT id, title, summary, SUBSTRING(content, 1, %s) AS content, "
            f"source, publish_time, topic_id, category_id, "
            f"MATCH(title, summary, content) AGAINST(%s IN BOOLEAN MODE) AS score "
            f"FROM news "
            f"WHERE MATCH(title, summary, content) AGAINST(%s IN BOOLEAN MODE) "
            f"AND id NOT IN ({placeholders}) AND status = 1 "
            f"ORDER BY score DESC LIMIT %s"
        )
        params = [CONTENT_TRUNCATE, keywords, keywords] + list(exclude) + [limit]
        rows = execute_query(sql, params)
        return [_row_to_news(r, "keyword_match") for r in (rows or [])]

    def _fulltext_search_posts(
        self, question: str, exclude_ids: set, limit: int
    ) -> List[SearchResultItem]:
        # 社区帖子没有全文索引，用 LIKE 搜索
        words = [w for w in question.strip().split() if len(w) >= 2]
        if not words:
            return []

        exclude = exclude_ids | {0}
        placeholders = ",".join(["%s"] * len(exclude))
        like_clauses = " OR ".join(["title LIKE %s OR content LIKE %s"] * len(words))
        like_params: List[Any] = []
        for w in words:
            like_params.extend([f"%{w}%", f"%{w}%"])

        sql = (
            f"SELECT p.id, p.title, SUBSTRING(p.content, 1, %s) AS content, "
            f"u.nickname, p.created_at, p.topic_id, p.related_news_id "
            f"FROM community_post p LEFT JOIN user u ON p.user_id = u.id "
            f"WHERE ({like_clauses}) AND p.id NOT IN ({placeholders}) AND p.status = 1 "
            f"ORDER BY p.heat_score DESC LIMIT %s"
        )
        params = [CONTENT_TRUNCATE] + like_params + list(exclude) + [limit]
        rows = execute_query(sql, params)
        return [_row_to_post(r, "keyword_match") for r in (rows or [])]

    # ══════════════════════════════════════════════════════
    # 辅助
    # ══════════════════════════════════════════════════════

    @staticmethod
    def _add_exclude(exclude: Dict[str, set], item: SearchResultItem) -> None:
        exclude.setdefault(item.type, set()).add(item.id)


# ══════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════

def _iso(dt) -> Optional[str]:
    if dt is None:
        return None
    return dt.isoformat() if hasattr(dt, "isoformat") else str(dt)


def _row_to_news(r: Dict[str, Any], relevance: str) -> SearchResultItem:
    return SearchResultItem(
        type="news",
        id=r["id"],
        title=r.get("title"),
        summary=r.get("summary"),
        content=(r.get("content") or "")[:CONTENT_TRUNCATE],
        source=r.get("source"),
        publishTime=_iso(r.get("publish_time")),
        topicId=r.get("topic_id"),
        categoryId=r.get("category_id"),
        relevance=relevance,
    )


def _row_to_post(r: Dict[str, Any], relevance: str) -> SearchResultItem:
    return SearchResultItem(
        type="community_post",
        id=r["id"],
        title=r.get("title"),
        content=(r.get("content") or "")[:CONTENT_TRUNCATE],
        source=r.get("nickname"),
        publishTime=_iso(r.get("created_at")),
        topicId=r.get("topic_id"),
        newsId=r.get("related_news_id"),
        relevance=relevance,
    )


def _item_to_dict(item: Optional[SearchResultItem]) -> Optional[Dict[str, Any]]:
    if item is None:
        return None
    return item.model_dump()


def _tokenize_for_fulltext(text: str) -> str:
    """将中文文本转换为 MySQL BOOLEAN MODE 全文搜索用的查询字符串"""
    # 简单策略: 每个连续中文字符块前面加 +，英文单词前面加 +
    import re
    tokens = re.findall(r'[一-鿿]{2,}|[a-zA-Z]{3,}', text)
    if not tokens:
        # 至少用原始文本
        return text.replace(" ", "").strip()
    return " ".join(f"+{t}" for t in tokens[:10])
