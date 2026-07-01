from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.exceptions import AIServiceException, register_exception_handlers
from app.core.config import settings
from app.routers.chat import router as chat_router
from app.routers.check import router as check_router
from app.routers.comment_summary import router as comment_summary_router
from app.routers.extract import router as extract_router
from app.routers.generate import router as generate_router
from app.routers.health import router as health_router
from app.routers.profile_report import router as profile_report_router
from app.routers.timeline import router as timeline_router

app = FastAPI(
    title=f"{settings.project_name} AI 服务",
    version="0.1.0",
    description="第 3 阶段 AI 服务基础框架与 Mock 接口。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get(f"{settings.api_prefix}/test-error", tags=["开发测试"])
async def test_error():
    """开发测试接口：主动抛出 AI 服务异常以验证统一处理。"""
    raise AIServiceException(code=400, message="AI 服务开发测试异常")

app.include_router(health_router)
app.include_router(generate_router)
app.include_router(extract_router)
app.include_router(check_router)
app.include_router(chat_router)
app.include_router(comment_summary_router)
app.include_router(profile_report_router)
app.include_router(timeline_router)
