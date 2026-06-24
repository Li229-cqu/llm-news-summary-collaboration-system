from typing import List, Optional
from datetime import datetime, timedelta
from app.modules.community.schema import (
    CommunityPost,
    CreatePostRequest,
    PostListResponse,
    CommentItem,
    CreateCommentRequest,
    CommentListResponse,
    HotSearchItem,
    AIHelperResponse,
    LikeResponse,
)
from app.mock.community import MOCK_COMMUNITY_POSTS

# 内存存储模拟
posts_db: List[CommunityPost] = []
comments_db: List[CommentItem] = []
post_likes: dict = {}
comment_likes: dict = {}

# 初始化mock数据
def init_mock_data():
    if not posts_db:
        for idx, mock_post in enumerate(MOCK_COMMUNITY_POSTS, 1):
            posts_db.append(CommunityPost(
                id=idx,
                title=mock_post["title"],
                content=mock_post["content"],
                author=mock_post["author"],
                author_id=1,
                created_at=datetime.now() - timedelta(hours=idx * 2),
                updated_at=datetime.now() - timedelta(hours=idx * 2),
                likes=10 + idx * 5,
                comments=3 + idx * 2,
                views=100 + idx * 20,
                tags=["AI", "新闻"] if idx == 1 else ["阅读", "讨论"],
            ))
    if not comments_db:
        for i in range(1, 6):
            comments_db.append(CommentItem(
                id=i,
                post_id=1 if i <= 3 else 2,
                content=f"这是评论 {i} 的内容",
                author=f"用户{i}",
                author_id=i,
                created_at=datetime.now() - timedelta(hours=i),
                likes=i * 2,
            ))

init_mock_data()


def create_post(request: CreatePostRequest, author_id: int = 1, author_name: str = "用户") -> CommunityPost:
    new_post = CommunityPost(
        id=len(posts_db) + 1,
        title=request.title,
        content=request.content,
        author=author_name,
        author_id=author_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        tags=request.tags or [],
    )
    posts_db.append(new_post)
    return new_post


def get_post_list(page: int = 1, page_size: int = 10) -> PostListResponse:
    sorted_posts = sorted(posts_db, key=lambda x: x.created_at, reverse=True)
    start = (page - 1) * page_size
    end = start + page_size
    return PostListResponse(
        list=sorted_posts[start:end],
        total=len(sorted_posts),
        page=page,
        page_size=page_size,
    )


def get_post_detail(post_id: int) -> Optional[CommunityPost]:
    for post in posts_db:
        if post.id == post_id:
            post.views += 1
            return post
    return None


def create_comment(post_id: int, request: CreateCommentRequest, author_id: int = 1, author_name: str = "用户") -> CommentItem:
    new_comment = CommentItem(
        id=len(comments_db) + 1,
        post_id=post_id,
        content=request.content,
        author=author_name,
        author_id=author_id,
        created_at=datetime.now(),
    )
    comments_db.append(new_comment)
    for post in posts_db:
        if post.id == post_id:
            post.comments += 1
            post.updated_at = datetime.now()
            break
    return new_comment


def get_comments(post_id: int, page: int = 1, page_size: int = 10) -> CommentListResponse:
    post_comments = [c for c in comments_db if c.post_id == post_id]
    sorted_comments = sorted(post_comments, key=lambda x: x.created_at, reverse=True)
    start = (page - 1) * page_size
    end = start + page_size
    return CommentListResponse(
        list=sorted_comments[start:end],
        total=len(sorted_comments),
        page=page,
        page_size=page_size,
    )


def toggle_post_like(post_id: int, user_id: int = 1) -> LikeResponse:
    key = f"{post_id}_{user_id}"
    if key in post_likes:
        del post_likes[key]
        for post in posts_db:
            if post.id == post_id:
                post.likes = max(0, post.likes - 1)
                return LikeResponse(success=True, liked=False, count=post.likes)
    else:
        post_likes[key] = True
        for post in posts_db:
            if post.id == post_id:
                post.likes += 1
                return LikeResponse(success=True, liked=True, count=post.likes)
    return LikeResponse(success=False, liked=False, count=0)


def get_hot_search(limit: int = 10) -> List[HotSearchItem]:
    hot_searches = [
        {"id": 1, "keyword": "AI新闻摘要", "search_count": 12580},
        {"id": 2, "keyword": "智能阅读", "search_count": 8920},
        {"id": 3, "keyword": "新闻分类", "search_count": 6750},
        {"id": 4, "keyword": "热门话题", "search_count": 5430},
        {"id": 5, "keyword": "资讯推荐", "search_count": 4210},
        {"id": 6, "keyword": "内容审核", "search_count": 3890},
        {"id": 7, "keyword": "新闻API", "search_count": 3120},
        {"id": 8, "keyword": "数据可视化", "search_count": 2560},
        {"id": 9, "keyword": "社交媒体", "search_count": 2130},
        {"id": 10, "keyword": "信息安全", "search_count": 1890},
    ]
    return [
        HotSearchItem(
            id=item["id"],
            keyword=item["keyword"],
            rank=i + 1,
            search_count=item["search_count"],
            trend="up" if i < 5 else "down" if i > 7 else "stable",
        )
        for i, item in enumerate(hot_searches[:limit])
    ]


def ai_news_helper(question: str) -> AIHelperResponse:
    responses = {
        "新闻摘要": "AI新闻摘要功能可以帮助您快速了解新闻核心内容，节省阅读时间。",
        "热点": "当前热点话题包括AI技术、智能阅读、新闻分类等，您可以在热搜榜查看详情。",
        "推荐": "根据您的阅读习惯，为您推荐相关新闻内容，请访问首页查看。",
        "帮助": "我是您的AI新闻助手，有什么可以帮助您的？",
    }
    
    for key in responses:
        if key in question:
            return AIHelperResponse(success=True, message="success", answer=responses[key])
    
    default_answer = (
        "感谢您的提问！我是AI新闻助手，专注于帮助您更好地获取和理解新闻资讯。"
        "如果您有关于新闻阅读、内容推荐或热点话题的问题，我可以为您解答。"
    )
    return AIHelperResponse(success=True, message="success", answer=default_answer)