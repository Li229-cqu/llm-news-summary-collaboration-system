import logging
import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.common.exceptions import AppException, register_exception_handlers
from app.common.response import success_response
from app.core.config import settings
from app.db.database import check_db_connection

logger = logging.getLogger(__name__)
_db_connected: bool = False

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
os.makedirs(os.path.join(str(UPLOADS_DIR), "avatar"), exist_ok=True)
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

# 自定义 JSON encoder，确保中文不被 escape
class ChineseJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

app.default_response_class = ChineseJSONResponse

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    return success_response(message="OK")


@app.on_event("startup")
async def startup_check() -> None:
    global _db_connected
    _db_connected = check_db_connection()
    if _db_connected:
        logger.info("数据库连接正常，系统使用真实数据库运行。")
    else:
        logger.warning(
            "\n"
            "╔══════════════════════════════════════════════════════╗\n"
            "║  ⚠️  数据库连接失败                                   ║\n"
            "║  系统将使用 Mock 数据运行，请检查 .env 配置           ║\n"
            "║  DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME ║\n"
            "╚══════════════════════════════════════════════════════╝"
        )


@app.get(f"{settings.api_prefix}/health", tags=["系统"])
async def health_check():
    """返回后端服务健康状态。"""
    return success_response(
        {
            "status": "ok",
            "service": "backend",
            "project": settings.project_name,
            "db_status": "connected" if _db_connected else "mock_mode",
        }
    )


@app.get(f"{settings.api_prefix}/test-error", tags=["开发测试"])
async def test_error():
    """开发测试接口：主动抛出业务异常以验证统一异常处理。"""
    raise AppException(code=400, message="开发测试异常")


app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(news_router)
app.include_router(interaction_router)
app.include_router(ai_router)
app.include_router(timeline_router)
app.include_router(community_router)
app.include_router(profile_router)
app.include_router(admin_router)
