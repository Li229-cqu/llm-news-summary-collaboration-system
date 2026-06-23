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

    # 以下字段仅为后续大模型接入预留，当前阶段不发起真实模型调用。
    llm_api_key: str = os.getenv("LLM_API_KEY", "your_api_key")
    llm_api_base_url: str = os.getenv("LLM_API_BASE_URL", "https://example.com")
    llm_model_name: str = os.getenv("LLM_MODEL_NAME", "mock-model")
    ai_mode: str = os.getenv("AI_MODE", "mock")

    @property
    def allowed_origins(self) -> list[str]:
        """允许后端与前端本地服务访问。"""
        return [self.backend_url, self.frontend_url]


settings = Settings()
