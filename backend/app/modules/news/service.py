"""新闻模块服务层。

当前从 Mock 数据读取新闻信息；后续接入数据库时，仅需将本文件中的数据查询逻辑替换为数据仓储查询。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.common.exceptions import AppException
from app.mock.news import (
    MOCK_BROWSE_HISTORY,
    MOCK_NEWS,
    MOCK_NEWS_FAVORITES,
    MOCK_NEWS_LIKES,
    NEWS_CATEGORIES,
)


def _get_current_user_id(current_user: Optional[Any]) -> Optional[int]:
    """兼容 Pydantic 用户模型与字典形式的当前用户数据。"""
    if current_user is None:
        return None
    if isinstance(current_user, dict):
        return current_user.get("id")
    return getattr(current_user, "id", None)


def _find_published_news(news_id: int) -> Optional[Dict[str, Any]]:
    """按 ID 查找已发布新闻。"""
    for news in MOCK_NEWS:
        if news["id"] == news_id and news["status"] == 1:
            return news
    return None


def _paginate(items: List[Dict[str, Any]], page: int, page_size: int) -> Dict[str, Any]:
    """对 Mock 列表执行稳定的内存分页。"""
    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    total = len(items)
    start = (normalized_page - 1) * normalized_page_size
    end = start + normalized_page_size

    return {
        "list": items[start:end],
        "total": total,
        "page": normalized_page,
        "page_size": normalized_page_size,
    }


def get_categories() -> List[Dict[str, Any]]:
    """获取启用的新闻分类，并按排序值升序返回。"""
    return sorted(
        (dict(category) for category in NEWS_CATEGORIES if category["status"] == 1),
        key=lambda category: category["sort"],
    )


def get_news_list(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """获取已发布新闻列表，支持分类、关键词和分页筛选。"""
    filtered_news = [dict(news) for news in MOCK_NEWS if news["status"] == 1]

    normalized_category = (category or "").strip().casefold()
    if normalized_category:
        filtered_news = [
            news
            for news in filtered_news
            if news["category_name"].casefold() == normalized_category
            or any(
                item["id"] == news["category_id"] and item["code"].casefold() == normalized_category
                for item in NEWS_CATEGORIES
            )
        ]

    normalized_keyword = (keyword or "").strip().casefold()
    if normalized_keyword:
        filtered_news = [
            news
            for news in filtered_news
            if normalized_keyword in news["title"].casefold()
            or normalized_keyword in news["summary"].casefold()
            or normalized_keyword in news["content"].casefold()
            or normalized_keyword in news["category_name"].casefold()
            or any(normalized_keyword in tag.casefold() for tag in news["tags"])
        ]

    filtered_news.sort(key=lambda news: (news["publish_time"], news["id"]), reverse=True)
    return _paginate(filtered_news, page=page, page_size=page_size)


def get_hot_news(limit: int = 10) -> List[Dict[str, Any]]:
    """按浏览、评论和点赞的综合热度返回新闻热榜。"""
    normalized_limit = max(limit, 0)
    published_news = [news for news in MOCK_NEWS if news["status"] == 1]
    sorted_news = sorted(
        published_news,
        key=lambda news: (
            news["view_count"] + news["comment_count"] * 100 + news["like_count"] * 10,
            news["view_count"],
            news["comment_count"],
            news["like_count"],
        ),
        reverse=True,
    )

    return [
        {
            "id": news["id"],
            "title": news["title"],
            "category_name": news["category_name"],
            "source": news["source"],
            "view_count": news["view_count"],
            "comment_count": news["comment_count"],
            "rank": index,
        }
        for index, news in enumerate(sorted_news[:normalized_limit], start=1)
    ]


def search_news(keyword: Optional[str], page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """按关键词搜索新闻；空关键词返回空分页结果。"""
    if not keyword or not keyword.strip():
        return _paginate([], page=page, page_size=page_size)
    return get_news_list(keyword=keyword, page=page, page_size=page_size)


def get_news_detail(news_id: int, current_user: Optional[Any] = None) -> Dict[str, Any]:
    """获取新闻详情及当前用户的点赞、收藏状态。"""
    news = _find_published_news(news_id)
    if news is None:
        raise AppException(code=404, message="新闻不存在")

    current_user_id = _get_current_user_id(current_user)
    detail = dict(news)
    detail["related_news"] = [
        dict(item)
        for item in MOCK_NEWS
        if item["status"] == 1
        and item["category_id"] == news["category_id"]
        and item["id"] != news["id"]
    ][:3]
    detail["recommended_news"] = [
        dict(item)
        for item in sorted(
            (item for item in MOCK_NEWS if item["status"] == 1 and item["id"] != news["id"]),
            key=lambda item: item["view_count"],
            reverse=True,
        )[:5]
    ]
    detail["is_liked"] = current_user_id is not None and any(
        item["user_id"] == current_user_id and item["news_id"] == news_id
        for item in MOCK_NEWS_LIKES
    )
    detail["is_favorited"] = current_user_id is not None and any(
        item["user_id"] == current_user_id and item["news_id"] == news_id
        for item in MOCK_NEWS_FAVORITES
    )
    return detail


def record_browse(news_id: int, current_user: Optional[Any] = None) -> Dict[str, Any]:
    """记录浏览行为；登录用户的记录暂时写入进程内 Mock 列表。"""
    if _find_published_news(news_id) is None:
        raise AppException(code=404, message="新闻不存在")

    current_user_id = _get_current_user_id(current_user)
    if current_user_id is not None:
        MOCK_BROWSE_HISTORY.append(
            {
                "user_id": current_user_id,
                "news_id": news_id,
                "browse_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return {"news_id": news_id, "recorded": True}
