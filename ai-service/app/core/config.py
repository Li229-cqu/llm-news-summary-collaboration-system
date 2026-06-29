from __future__ import annotations

from typing import List
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Settings(BaseModel):
    """基于大语言模型的智能新闻摘要与协同互动系统 AI 服务配置。"""

    project_name: str = os.getenv("PROJECT_NAME", "基于大语言模型的智能新闻摘要与协同互动系统")
    service_name: str = os.getenv("SERVICE_NAME", "ai-service")
    api_prefix: str = os.getenv("AI_API_PREFIX", "/ai")
    ai_service_host: str = os.getenv("AI_SERVICE_HOST", "127.0.0.1")
    ai_service_port: int = int(os.getenv("AI_SERVICE_PORT", "8001"))
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    ai_mode: str = os.getenv("AI_MODE", "mock")

    # LLM 配置（阶段 9.1 新增，当前阶段仅配置准备，不发起真实调用）
    llm_enabled: bool = os.getenv("LLM_ENABLED", "false").lower() == "true"
    llm_provider: str = os.getenv("LLM_PROVIDER", "zhipu")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
    llm_model: str = os.getenv("LLM_MODEL", "glm-4-flash")
    llm_timeout: int = int(os.getenv("LLM_TIMEOUT", "30"))
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    llm_thinking_type: str = os.getenv("LLM_THINKING_TYPE", "disabled")

    @property
    def allowed_origins(self) -> list[str]:
        """允许后端与前端本地服务访问。"""
        return [self.backend_url, self.frontend_url]


settings = Settings()
