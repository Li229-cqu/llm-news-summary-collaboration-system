"""个人中心模块服务层。

当前从 Mock 数据读取用户相关信息；后续接入数据库时，仅需将本文件中的数据查询逻辑替换为数据仓储查询。
"""

from typing import Any, Dict, List, Optional

from app.mock.ai_records import MOCK_AI_RECORDS
from app.mock.comments import MOCK_NEWS_COMMENTS
from app.mock.news import MOCK_BROWSE_HISTORY, MOCK_NEWS, MOCK_NEWS_FAVORITES
from app.modules.profile.schema import (
    AIRecordItem,
    BrowseHistoryItem,
    FavoriteItem,
    ProfileOverview,
    ProfileTestData,
)


def get_test_data() -> ProfileTestData:
    return ProfileTestData(module="profile", description="个人中心模块基础接口占位")


def _get_current_user_id(current_user: Optional[Any]) -> Optional[int]:
    """兼容 Pydantic 用户模型与字典形式的当前用户数据。"""
    if current_user is None:
        return None
    if isinstance(current_user, dict):
        return current_user.get("id")
    return getattr(current_user, "id", None)


def _paginate(items: List[dict], page: int, page_size: int) -> Dict[str, Any]:
    """对列表执行稳定的内存分页。"""
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


def get_profile_overview(current_user: Optional[Any] = None) -> ProfileOverview:
    """获取个人中心概览数据。"""
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return ProfileOverview(
            user_id=0,
            browse_count=0,
            favorite_count=0,
            comment_count=0,
            ai_generate_count=0,
        )

    browse_count = sum(1 for item in MOCK_BROWSE_HISTORY if item["user_id"] == user_id)
    favorite_count = sum(1 for item in MOCK_NEWS_FAVORITES if item["user_id"] == user_id)
    comment_count = sum(1 for item in MOCK_NEWS_COMMENTS if item["user_id"] == user_id)
    # 兼容早期 AI 历史数据：当时记录尚未保存 user_id，默认归属当前 mock 普通用户。
    ai_generate_count = sum(
        1 for item in MOCK_AI_RECORDS if item.get("user_id", 1) == user_id
    )

    return ProfileOverview(
        user_id=user_id,
        browse_count=browse_count,
        favorite_count=favorite_count,
        comment_count=comment_count,
        ai_generate_count=ai_generate_count,
    )


def get_browse_history(
    current_user: Optional[Any] = None, page: int = 1, page_size: int = 10
) -> Dict[str, Any]:
    """获取用户浏览历史。"""
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return _paginate([], page=page, page_size=page_size)

    user_history = [item for item in MOCK_BROWSE_HISTORY if item["user_id"] == user_id]
    user_history.sort(key=lambda x: x["browse_time"], reverse=True)

    news_map = {news["id"]: news for news in MOCK_NEWS}

    history_items = []
    for record in user_history:
        news = news_map.get(record["news_id"])
        if news:
            history_items.append(
                BrowseHistoryItem(
                    news_id=news["id"],
                    title=news["title"],
                    category_name=news["category_name"],
                    browse_time=record["browse_time"],
                ).dict()
            )

    return _paginate(history_items, page=page, page_size=page_size)


def get_favorites(
    current_user: Optional[Any] = None, page: int = 1, page_size: int = 10
) -> Dict[str, Any]:
    """获取用户收藏列表。"""
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return _paginate([], page=page, page_size=page_size)

    user_favorites = [item for item in MOCK_NEWS_FAVORITES if item["user_id"] == user_id]

    news_map = {news["id"]: news for news in MOCK_NEWS}

    favorite_items = []
    for record in user_favorites:
        news = news_map.get(record["news_id"])
        if news:
            favorite_items.append(
                FavoriteItem(
                    news_id=news["id"],
                    title=news["title"],
                    summary=news["summary"],
                    category_name=news["category_name"],
                    source=news["source"],
                    publish_time=news["publish_time"],
                ).dict()
            )

    favorite_items.sort(key=lambda x: x["publish_time"], reverse=True)

    return _paginate(favorite_items, page=page, page_size=page_size)


def get_ai_records(
    current_user: Optional[Any] = None, page: int = 1, page_size: int = 10
) -> Dict[str, Any]:
    """获取用户 AI 生成记录。"""
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return _paginate([], page=page, page_size=page_size)

    # 新版记录保存 user_id；旧版记录没有该字段时按 mock 普通用户处理。
    user_records = [
        item for item in MOCK_AI_RECORDS if item.get("user_id", 1) == user_id
    ]
    user_records.sort(key=lambda x: x.get("id", 0), reverse=True)

    record_items = []
    for record in user_records:
        result = record.get("result", record)
        record_items.append(
            AIRecordItem(
                id=record["id"],
                input_text=record["input_text"],
                candidate_titles=result.get("candidate_titles", []),
                summary_short=result.get("summary_short", ""),
                summary_long=result.get("summary_long"),
                create_time=record.get("create_time") or record.get("created_at"),
            ).dict()
        )

    return _paginate(record_items, page=page, page_size=page_size)
