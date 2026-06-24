"""管理后台模块服务层。

当前从 Mock 数据读取管理相关信息；后续接入数据库时，仅需将本文件中的数据查询逻辑替换为数据仓储查询。
"""

from typing import Any, Dict, List, Optional

from app.mock.community import MOCK_COMMUNITY_POSTS
from app.mock.news import MOCK_NEWS
from app.mock.users import MOCK_USERS
from app.modules.admin.schema import AdminDashboard, AdminTestData, UserItem


def get_test_data() -> AdminTestData:
    return AdminTestData(module="admin", description="管理后台模块基础接口占位")


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


def get_dashboard() -> AdminDashboard:
    """获取后台概览数据。"""
    user_count = len(MOCK_USERS)
    news_count = len([news for news in MOCK_NEWS if news["status"] == 1])
    post_count = len(MOCK_COMMUNITY_POSTS)
    pending_count = len([post for post in MOCK_COMMUNITY_POSTS if post["status"] == 0])

    return AdminDashboard(
        user_count=user_count,
        news_count=news_count,
        post_count=post_count,
        pending_count=pending_count,
    )


def get_pending_posts(page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """获取待审核帖子列表。"""
    pending_posts = [
        post for post in MOCK_COMMUNITY_POSTS if post["status"] == 0
    ]
    pending_posts.sort(key=lambda x: x.get("create_time", ""), reverse=True)

    return _paginate(pending_posts, page=page, page_size=page_size)


def get_users(page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """获取用户管理列表。"""
    user_items = []
    for user in MOCK_USERS:
        user_items.append(
            UserItem(
                id=user["id"],
                username=user["username"],
                nickname=user["nickname"],
                role=user["role"],
                status=user["status"],
            ).dict()
        )

    user_items.sort(key=lambda x: x["id"])

    return _paginate(user_items, page=page, page_size=page_size)


def get_system_config() -> Dict[str, Any]:
    """获取系统配置（Mock 数据）。"""
    return {
        "site_name": "智能新闻摘要系统",
        "site_description": "基于大语言模型的智能新闻摘要与协同互动系统",
        "max_upload_size": 10,
        "default_page_size": 10,
        "ai_service_enabled": True,
        "auto_approve_enabled": False,
    }
