from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """单个 LLM 模型配置。"""
    enabled: bool = False
    provider: str = ""
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    timeout: int = 30
    temperature: float = 0.3
    max_tokens: int = 2048


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

    summary_llm_enabled: bool = os.getenv("SUMMARY_LLM_ENABLED", "false").lower() == "true"
    summary_llm_provider: str = os.getenv("SUMMARY_LLM_PROVIDER", "deepseek")
    summary_llm_api_key: str = os.getenv("SUMMARY_LLM_API_KEY", "")
    summary_llm_base_url: str = os.getenv("SUMMARY_LLM_BASE_URL", "https://api.deepseek.com/v1")
    summary_llm_model: str = os.getenv("SUMMARY_LLM_MODEL", "deepseek-chat")
    summary_llm_timeout: int = int(os.getenv("SUMMARY_LLM_TIMEOUT", "60"))
    summary_llm_temperature: float = float(os.getenv("SUMMARY_LLM_TEMPERATURE", "0.3"))
    summary_llm_max_tokens: int = int(os.getenv("SUMMARY_LLM_MAX_TOKENS", "2048"))

    evidence_llm_enabled: bool = os.getenv("EVIDENCE_LLM_ENABLED", "false").lower() == "true"
    evidence_llm_provider: str = os.getenv("EVIDENCE_LLM_PROVIDER", "zhipu")
    evidence_llm_api_key: str = os.getenv("EVIDENCE_LLM_API_KEY", "")
    evidence_llm_base_url: str = os.getenv("EVIDENCE_LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
    evidence_llm_model: str = os.getenv("EVIDENCE_LLM_MODEL", "GLM-5.2")
    evidence_llm_timeout: int = int(os.getenv("EVIDENCE_LLM_TIMEOUT", "45"))
    evidence_llm_temperature: float = float(os.getenv("EVIDENCE_LLM_TEMPERATURE", "0.1"))
    evidence_llm_max_tokens: int = int(os.getenv("EVIDENCE_LLM_MAX_TOKENS", "4096"))

    # --- 通用 LLM 参数（非配置，仅工具字段） ---
    llm_thinking_type: str = os.getenv("LLM_THINKING_TYPE", "disabled")

    @property
    def allowed_origins(self) -> list[str]:
        """允许后端与前端本地服务访问。"""
        return [self.backend_url, self.frontend_url]

    @property
    def summary_llm_config(self) -> LLMConfig:
        """返回摘要生成器的 LLM 配置。"""
        return LLMConfig(
            enabled=self.summary_llm_enabled,
            provider=self.summary_llm_provider,
            api_key=self.summary_llm_api_key,
            base_url=self.summary_llm_base_url,
            model=self.summary_llm_model,
            timeout=self.summary_llm_timeout,
            temperature=self.summary_llm_temperature,
            max_tokens=self.summary_llm_max_tokens,
        )

    @property
    def evidence_llm_config(self) -> LLMConfig:
        """返回证据评估器的 LLM 配置。"""
        return LLMConfig(
            enabled=self.evidence_llm_enabled,
            provider=self.evidence_llm_provider,
            api_key=self.evidence_llm_api_key,
            base_url=self.evidence_llm_base_url,
            model=self.evidence_llm_model,
            timeout=self.evidence_llm_timeout,
            temperature=self.evidence_llm_temperature,
            max_tokens=self.evidence_llm_max_tokens,
        )


def load_config_from_backend(backend_url: str) -> Dict[str, Any]:
    """从后端 API 获取 AI 配置。"""
    try:
        import httpx
        url = f"{backend_url.rstrip('/')}/api/admin/ai-config"
        with httpx.Client(timeout=5) as client:
            response = client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {})
    except Exception as e:
        logger.warning(f"从后端加载配置失败，将使用 .env 配置: {e}")
    return {}


def apply_backend_config(settings: Settings, backend_config: Dict[str, Any]) -> Settings:
    """将后端配置应用到 settings 对象。"""
    if not backend_config:
        return settings

    if backend_config.get('enable_real_llm') is not None:
        settings.summary_llm_enabled = backend_config['enable_real_llm']
        settings.evidence_llm_enabled = backend_config['enable_real_llm']

    if backend_config.get('timeout') is not None:
        settings.summary_llm_timeout = backend_config['timeout']
        settings.evidence_llm_timeout = backend_config['timeout']

    if backend_config.get('model_name'):
        settings.summary_llm_model = backend_config['model_name']
        settings.evidence_llm_model = backend_config['model_name']

    if backend_config.get('service_url'):
        pass

    logger.info("AI 配置已从后端同步")
    return settings


def reload_settings_from_env(settings: Settings) -> Settings:
    """Reload AI configuration from ai-service/.env only."""
    load_dotenv(BASE_DIR / ".env", override=True)

    settings.summary_llm_enabled = os.getenv("SUMMARY_LLM_ENABLED", "false").lower() == "true"
    settings.summary_llm_provider = os.getenv("SUMMARY_LLM_PROVIDER", "deepseek")
    settings.summary_llm_api_key = os.getenv("SUMMARY_LLM_API_KEY", "")
    settings.summary_llm_base_url = os.getenv("SUMMARY_LLM_BASE_URL", "https://api.deepseek.com/v1")
    settings.summary_llm_model = os.getenv("SUMMARY_LLM_MODEL", "deepseek-chat")
    settings.summary_llm_timeout = int(os.getenv("SUMMARY_LLM_TIMEOUT", "45"))
    settings.summary_llm_temperature = float(os.getenv("SUMMARY_LLM_TEMPERATURE", "0.3"))
    settings.summary_llm_max_tokens = int(os.getenv("SUMMARY_LLM_MAX_TOKENS", "2048"))

    settings.evidence_llm_enabled = os.getenv("EVIDENCE_LLM_ENABLED", "false").lower() == "true"
    settings.evidence_llm_provider = os.getenv("EVIDENCE_LLM_PROVIDER", "zhipu")
    settings.evidence_llm_api_key = os.getenv("EVIDENCE_LLM_API_KEY", "")
    settings.evidence_llm_base_url = os.getenv("EVIDENCE_LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
    settings.evidence_llm_model = os.getenv("EVIDENCE_LLM_MODEL", "GLM-5.2")
    settings.evidence_llm_timeout = int(os.getenv("EVIDENCE_LLM_TIMEOUT", "45"))
    settings.evidence_llm_temperature = float(os.getenv("EVIDENCE_LLM_TEMPERATURE", "0.1"))
    settings.evidence_llm_max_tokens = int(os.getenv("EVIDENCE_LLM_MAX_TOKENS", "4096"))
    settings.llm_thinking_type = os.getenv("LLM_THINKING_TYPE", "disabled")
    logger.info("AI config reloaded from ai-service/.env")
    return settings


settings = Settings()
