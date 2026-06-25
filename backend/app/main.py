from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.exceptions import AppException, register_exception_handlers
from app.common.response import success_response
from app.core.config import settings
from app.modules.admin.router import router as admin_router
from app.modules.ai.router import router as ai_router
from app.modules.auth.router import router as auth_router
from app.modules.community.router import router as community_router
from app.modules.interaction.router import router as interaction_router
from app.modules.news.router import router as news_router
from app.modules.profile.router import router as profile_router
from app.modules.timeline.router import router as timeline_router
from app.modules.user.router import router as user_router

app = FastAPI(
    title=f"{settings.project_name}后端服务",
    version="0.1.0",
    description="第 2 阶段后端基础框架与占位接口。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get(f"{settings.api_prefix}/health", tags=["系统"])
async def health_check():
    """返回后端服务健康状态。"""
    return success_response(
        {
            "status": "ok",
            "service": "backend",
            "project": settings.project_name,
        }
    )


@app.get(f"{settings.api_prefix}/test-error", tags=["开发测试"])
async def test_error():
    """开发测试接口：主动抛出业务异常以验证统一异常处理。"""
    raise AppException(code=400, message="开发测试异常")


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(news_router)
app.include_router(interaction_router)
app.include_router(ai_router)
app.include_router(timeline_router)
app.include_router(community_router)
app.include_router(profile_router)
app.include_router(admin_router)
