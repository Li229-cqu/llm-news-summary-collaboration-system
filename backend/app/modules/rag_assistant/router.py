"""RAG Assistant Router — POST /api/assistant/search"""

from __future__ import annotations

import logging
import json
from fastapi import APIRouter
from app.common.response import success_response, error_response
from app.modules.rag_assistant.schema import SearchRequest
from app.modules.rag_assistant.rag import MultiResourceRetriever, _item_to_dict

logger = logging.getLogger(__name__)

router = APIRouter(tags=["RAG Assistant"])

retriever = MultiResourceRetriever()


@router.get("/api/search")
async def unified_search(q: str = "", page: int = 1, pageSize: int = 20):
    """统一搜索 — 同时检索新闻和社区帖子，返回分类结果"""
    question = q.strip()
    if not question:
        return success_response({"news": [], "posts": [], "totalNews": 0, "totalPosts": 0})

    logger.info("[RAG-Search] 统一搜索: q=%s page=%d", question, page)

    try:
        # 直接用全文搜索，不走 Step0/Step1 上下文检索
        news_results = retriever._fulltext_search_news(question, set(), pageSize)
        post_results = retriever._fulltext_search_posts(question, set(), pageSize)
    except Exception as e:
        logger.error("[RAG-Search] 搜索异常: %s", e)
        return error_response(code=500, message=f"搜索失败: {str(e)}")

    result = {
        "news": [_item_to_dict(r) for r in news_results],
        "posts": [_item_to_dict(r) for r in post_results],
        "totalNews": len(news_results),
        "totalPosts": len(post_results),
    }
    logger.info("[RAG-Search] 结果: news=%d posts=%d", len(news_results), len(post_results))
    return success_response(result)


@router.post("/api/assistant/search")
async def search_assistant(payload: SearchRequest):
    """检索与用户问题相关的新闻、帖子、评论等内容"""
    # ── 日志：记录前端发来的请求 ──
    ctx = payload.context.model_dump() if payload.context else {}
    logger.info(
        "[RAG] ┌─ 前端请求 ─────────────────────────────\n"
        "[RAG] │ POST /api/assistant/search\n"
        "[RAG] │ question: %s\n"
        "[RAG] │ context: %s\n"
        "[RAG] └──────────────────────────────────────",
        payload.question,
        json.dumps(ctx, ensure_ascii=False),
    )

    try:
        result = await retriever.retrieve(
            question=payload.question,
            context=ctx,
        )

        # ── 日志：记录返回给前端的结果摘要 ──
        articles = result.get("articles", [])
        current = result.get("current")
        logger.info(
            "[RAG] ┌─ 返回前端 ─────────────────────────────\n"
            "[RAG] │ current: %s\n"
            "[RAG] │ articles: %d 条\n"
            "[RAG] └──────────────────────────────────────",
            json.dumps(current, ensure_ascii=False)[:200] if current else "null",
            len(articles),
        )

        return success_response(result)
    except Exception as e:
        logger.error("[RAG] 检索异常: %s", e, exc_info=True)
        return error_response(code=500, message=f"检索失败: {str(e)}")
