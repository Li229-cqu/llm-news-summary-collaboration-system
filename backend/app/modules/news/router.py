"""新闻模块接口路由。"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, Query

from app.common.auth import require_login
from app.common.response import ApiResponse, success_response
from app.modules.auth.schema import UserInfo
from app.modules.auth.service import get_mock_user_by_token
from app.modules.news.service import (
    get_categories,
    get_hot_news,
    get_news_detail,
    get_news_list,
    get_subscribed_news,
    record_browse,
    search_news,
)

router = APIRouter(prefix="/api/news", tags=["news"])


def _get_optional_current_user(authorization: Optional[str]) -> Optional[UserInfo]:
    if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    return get_mock_user_by_token(token)


@router.get("/ping", response_model=ApiResponse[str])
async def ping_news() -> ApiResponse[str]:
    return success_response("news module ok")


@router.get("/categories")
async def news_categories() -> ApiResponse[Any]:
    return success_response(get_categories())


@router.get("")
async def news_list(
    category: Optional[str] = Query(default=None),
    category_id: Optional[int] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1),
) -> ApiResponse[Any]:
    return success_response(
        get_news_list(
            category=category,
            category_id=category_id,
            keyword=keyword,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/hot")
async def hot_news(
    limit: int = Query(default=10, ge=0),
    category_id: Optional[int] = Query(default=None),
) -> ApiResponse[Any]:
    return success_response(get_hot_news(limit=limit, category_id=category_id))


@router.get("/search")
async def news_search(
    keyword: str = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1),
) -> ApiResponse[Any]:
    return success_response(search_news(keyword=keyword, page=page, page_size=page_size))

@router.get("/subscribed")
async def subscribed_news(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[Any]:
    return success_response(
        get_subscribed_news(current_user=current_user, page=page, page_size=page_size)
    )

@router.get("/{news_id}")
async def news_detail(
    news_id: int,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> ApiResponse[Any]:
    current_user = _get_optional_current_user(authorization)
    return success_response(get_news_detail(news_id=news_id, current_user=current_user))


@router.post("/{news_id}/browse")
async def browse_news(
    news_id: int,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> ApiResponse[Any]:
    current_user = _get_optional_current_user(authorization)
    return success_response(record_browse(news_id=news_id, current_user=current_user))
