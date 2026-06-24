"""新闻互动模块服务层。

当前服务直接读写进程内 Mock 数据；后续接入数据库时可替换为对应的数据仓储操作。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.common.exceptions import AppException
from app.mock.comments import MOCK_COMMENT_LIKES, MOCK_NEWS_COMMENTS
from app.mock.news import MOCK_NEWS, MOCK_NEWS_FAVORITES, MOCK_NEWS_LIKES
from app.modules.interaction.schema import (
    CommentCreateRequest,
    CommentItem,
    CommentLikeResult,
    CommentListResponse,
    CommentReplyRequest,
    InteractionResult,
    InteractionTestData,
)


def get_test_data() -> InteractionTestData:
    """保留模块连通性测试的占位数据。"""
    return InteractionTestData(module="interaction", description="新闻互动模块基础接口占位")


def require_current_user(current_user: Optional[Any]) -> Any:
    """校验互动写操作的当前用户。"""
    user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
    if current_user is None or user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")
    return current_user


def _get_current_user_value(current_user: Any, field: str, default: Any = "") -> Any:
    if isinstance(current_user, dict):
        return current_user.get(field, default)
    return getattr(current_user, field, default)


def get_news_by_id(news_id: int) -> Dict[str, Any]:
    """获取可参与互动的已发布新闻。"""
    for news in MOCK_NEWS:
        if news["id"] == news_id and news["status"] == 1:
            return news
    raise AppException(code=404, message="新闻不存在")


def get_comment_by_id(comment_id: int) -> Dict[str, Any]:
    """获取未删除的评论。"""
    for comment in MOCK_NEWS_COMMENTS:
        if comment["id"] == comment_id and comment["status"] != 4:
            return comment
    raise AppException(code=404, message="评论不存在")


def get_next_comment_id() -> int:
    """生成当前 Mock 数据中的下一个评论 ID。"""
    return max((comment["id"] for comment in MOCK_NEWS_COMMENTS), default=0) + 1


def _has_news_relation(relations: List[Dict[str, int]], user_id: int, news_id: int) -> bool:
    return any(item["user_id"] == user_id and item["news_id"] == news_id for item in relations)


def _remove_news_relation(relations: List[Dict[str, int]], user_id: int, news_id: int) -> bool:
    for index, item in enumerate(relations):
        if item["user_id"] == user_id and item["news_id"] == news_id:
            relations.pop(index)
            return True
    return False


def is_comment_liked(comment_id: int, current_user: Optional[Any]) -> bool:
    """判断当前用户是否已点赞指定评论。"""
    if current_user is None:
        return False
    user_id = _get_current_user_value(current_user, "id", None)
    if user_id is None:
        return False
    return any(
        item["user_id"] == user_id and item["comment_id"] == comment_id
        for item in MOCK_COMMENT_LIKES
    )


def like_news(news_id: int, current_user: Optional[Any]) -> InteractionResult:
    """点赞新闻；重复调用保持点赞数量不变。"""
    user = require_current_user(current_user)
    news = get_news_by_id(news_id)
    user_id = _get_current_user_value(user, "id")

    if _has_news_relation(MOCK_NEWS_LIKES, user_id, news_id):
        return InteractionResult(
            target_id=news_id,
            target_type="news",
            action="like",
            status=True,
            like_count=news["like_count"],
            message="已点赞",
        )

    MOCK_NEWS_LIKES.append({"user_id": user_id, "news_id": news_id})
    news["like_count"] += 1
    return InteractionResult(
        target_id=news_id,
        target_type="news",
        action="like",
        status=True,
        like_count=news["like_count"],
        message="点赞成功",
    )


def unlike_news(news_id: int, current_user: Optional[Any]) -> InteractionResult:
    """取消新闻点赞；未点赞时保持未点赞状态。"""
    user = require_current_user(current_user)
    news = get_news_by_id(news_id)
    user_id = _get_current_user_value(user, "id")
    removed = _remove_news_relation(MOCK_NEWS_LIKES, user_id, news_id)
    if removed:
        news["like_count"] = max(news["like_count"] - 1, 0)

    return InteractionResult(
        target_id=news_id,
        target_type="news",
        action="unlike",
        status=False,
        like_count=news["like_count"],
        message="已取消点赞" if removed else "当前未点赞",
    )


def favorite_news(news_id: int, current_user: Optional[Any]) -> InteractionResult:
    """收藏新闻；重复调用保持收藏数量不变。"""
    user = require_current_user(current_user)
    news = get_news_by_id(news_id)
    user_id = _get_current_user_value(user, "id")

    if _has_news_relation(MOCK_NEWS_FAVORITES, user_id, news_id):
        return InteractionResult(
            target_id=news_id,
            target_type="news",
            action="favorite",
            status=True,
            favorite_count=news["favorite_count"],
            message="已收藏",
        )

    MOCK_NEWS_FAVORITES.append({"user_id": user_id, "news_id": news_id})
    news["favorite_count"] += 1
    return InteractionResult(
        target_id=news_id,
        target_type="news",
        action="favorite",
        status=True,
        favorite_count=news["favorite_count"],
        message="收藏成功",
    )


def unfavorite_news(news_id: int, current_user: Optional[Any]) -> InteractionResult:
    """取消新闻收藏；未收藏时保持未收藏状态。"""
    user = require_current_user(current_user)
    news = get_news_by_id(news_id)
    user_id = _get_current_user_value(user, "id")
    removed = _remove_news_relation(MOCK_NEWS_FAVORITES, user_id, news_id)
    if removed:
        news["favorite_count"] = max(news["favorite_count"] - 1, 0)

    return InteractionResult(
        target_id=news_id,
        target_type="news",
        action="unfavorite",
        status=False,
        favorite_count=news["favorite_count"],
        message="已取消收藏" if removed else "当前未收藏",
    )


def build_comment_tree(news_id: int, current_user: Optional[Any] = None) -> CommentListResponse:
    """按 parent_id 将指定新闻的扁平评论组装为树形结构。"""
    visible_comments = [
        comment
        for comment in MOCK_NEWS_COMMENTS
        if comment["news_id"] == news_id and comment["status"] != 4
    ]
    comment_map: Dict[int, Dict[str, Any]] = {}
    for comment in visible_comments:
        item = dict(comment)
        if item["status"] == 2:
            item["content"] = "该评论已被折叠"
        item["is_liked"] = is_comment_liked(item["id"], current_user)
        item["replies"] = []
        comment_map[item["id"]] = item

    root_comments: List[Dict[str, Any]] = []
    for item in comment_map.values():
        parent_id = item["parent_id"]
        if parent_id is None or parent_id not in comment_map:
            root_comments.append(item)
        else:
            comment_map[parent_id]["replies"].append(item)

    root_comments.sort(key=lambda item: (item["create_time"], item["id"]))
    for item in comment_map.values():
        item["replies"].sort(key=lambda reply: (reply["create_time"], reply["id"]))

    return CommentListResponse(list=root_comments, total=len(visible_comments))


def get_news_comments(news_id: int, current_user: Optional[Any] = None) -> CommentListResponse:
    """获取新闻评论树；删除评论不展示，折叠评论使用固定提示文本。"""
    get_news_by_id(news_id)
    return build_comment_tree(news_id=news_id, current_user=current_user)


def _validate_comment_content(content: str) -> str:
    normalized_content = content.strip()
    if not normalized_content:
        raise AppException(code=400, message="评论内容不能为空")
    return normalized_content


def _create_comment_record(
    news_id: int,
    content: str,
    current_user: Any,
    parent_id: Optional[int] = None,
) -> CommentItem:
    news = get_news_by_id(news_id)
    user_id = _get_current_user_value(current_user, "id")
    comment = {
        "id": get_next_comment_id(),
        "news_id": news_id,
        "user_id": user_id,
        "username": _get_current_user_value(current_user, "username"),
        "nickname": _get_current_user_value(current_user, "nickname"),
        "avatar": _get_current_user_value(current_user, "avatar"),
        "parent_id": parent_id,
        "content": content,
        "like_count": 0,
        "status": 1,
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    MOCK_NEWS_COMMENTS.append(comment)
    news["comment_count"] += 1
    return CommentItem(**comment, is_liked=False, replies=[])


def create_news_comment(
    news_id: int,
    request: CommentCreateRequest,
    current_user: Optional[Any],
) -> CommentItem:
    """发布一级新闻评论。"""
    user = require_current_user(current_user)
    return _create_comment_record(
        news_id=news_id,
        content=_validate_comment_content(request.content),
        current_user=user,
    )


def reply_comment(
    comment_id: int,
    request: CommentReplyRequest,
    current_user: Optional[Any],
) -> CommentItem:
    """回复指定评论。"""
    user = require_current_user(current_user)
    parent_comment = get_comment_by_id(comment_id)
    return _create_comment_record(
        news_id=parent_comment["news_id"],
        content=_validate_comment_content(request.content),
        current_user=user,
        parent_id=comment_id,
    )


def like_comment(comment_id: int, current_user: Optional[Any]) -> CommentLikeResult:
    """点赞评论；重复调用保持点赞数量不变。"""
    user = require_current_user(current_user)
    comment = get_comment_by_id(comment_id)
    user_id = _get_current_user_value(user, "id")
    if is_comment_liked(comment_id, user):
        return CommentLikeResult(
            comment_id=comment_id,
            liked=True,
            like_count=comment["like_count"],
        )

    MOCK_COMMENT_LIKES.append({"user_id": user_id, "comment_id": comment_id})
    comment["like_count"] += 1
    return CommentLikeResult(
        comment_id=comment_id,
        liked=True,
        like_count=comment["like_count"],
    )
