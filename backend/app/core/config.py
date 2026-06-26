from __future__ import annotations

from typing import List
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Settings(BaseModel):
    """基于大语言模型的智能新闻摘要与协同互动系统后端配置。"""

    project_name: str = os.getenv("PROJECT_NAME", "基于大语言模型的智能新闻摘要与协同互动系统")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    backend_host: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # 当前阶段仅预留 AI 服务地址，不发起调用。
    ai_service_url: str = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
    # 当前阶段仅使用开发占位值，不应在生产环境使用该默认值。
    secret_key: str = os.getenv("SECRET_KEY", "dev_secret_key")

    # 当前阶段仅预留数据库配置，不建立数据库连接。
    db_host: str = os.getenv("DB_HOST", "127.0.0.1")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_name: str = os.getenv("DB_NAME", "llm_news_system")
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "your_password")

    @property
    def allowed_origins(self) -> list[str]:
        """当前阶段允许的前端跨域地址。"""
        return [self.frontend_url]


settings = Settings()
