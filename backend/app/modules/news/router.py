"""新闻模块接口路由。"""

from typing import Any, Optional

from fastapi import APIRouter, Header

from app.common.response import ApiResponse, success_response
from app.modules.auth.schema import UserInfo
from app.modules.auth.service import get_mock_user_by_token
from app.modules.news.service import (
    get_categories,
    get_hot_news,
    get_news_detail,
    get_news_list,
    record_browse,
    search_news,
)

router = APIRouter(prefix="/api/news", tags=["news"])


def _get_optional_current_user(authorization: Optional[str]) -> Optional[UserInfo]:
    """解析可选 Mock Token；解析失败时按未登录用户处理。"""
    if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    return get_mock_user_by_token(token)


@router.get("/ping", response_model=ApiResponse[str])
async def ping_news() -> ApiResponse[str]:
    """新闻模块基础连通性测试接口。"""
    return success_response("news module ok")


@router.get("/categories")
async def news_categories() -> ApiResponse[Any]:
    """获取启用的新闻分类。"""
    return success_response(get_categories())


@router.get("")
async def news_list(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> ApiResponse[Any]:
    """获取新闻列表。"""
    return success_response(
        get_news_list(
            category=category,
            keyword=keyword,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/hot")
async def hot_news(limit: int = 10) -> ApiResponse[Any]:
    """获取新闻热榜。"""
    return success_response(get_hot_news(limit=limit))


@router.get("/search")
async def news_search(
    keyword: str,
    page: int = 1,
    page_size: int = 10,
) -> ApiResponse[Any]:
    """按关键词搜索新闻。"""
    return success_response(search_news(keyword=keyword, page=page, page_size=page_size))


@router.get("/{news_id}")
async def news_detail(
    news_id: int,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> ApiResponse[Any]:
    """获取新闻详情；认证信息仅用于补充互动状态。"""
    current_user = _get_optional_current_user(authorization)
    return success_response(get_news_detail(news_id=news_id, current_user=current_user))


@router.post("/{news_id}/browse")
async def browse_news(
    news_id: int,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> ApiResponse[Any]:
    """记录新闻浏览行为；未登录访问同样会得到成功响应。"""
    current_user = _get_optional_current_user(authorization)
    return success_response(record_browse(news_id=news_id, current_user=current_user))
