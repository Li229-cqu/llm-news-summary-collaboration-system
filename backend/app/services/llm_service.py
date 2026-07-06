"""LLM Service — 直接调用大模型 API（OpenAI 兼容协议）。

Phase 1 升级：支持多 Provider（deepseek / zhipu），按步骤职责分流。
- DeepSeek = 生成类任务（出题老师）
- Zhipu   = 审核类任务（审题老师）

每个 provider 有独立的 API key、base URL、model、timeout，
Provider config is loaded from ai-service/.env.

Usage:
    from app.services.llm_service import llm_service
    result = await llm_service.chat_json("你是一个编辑...", "...", provider="deepseek")
"""

from __future__ import annotations

import json
import logging
import os
import re as _re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv

from app.core.llm_provider_policy import get_provider_defaults
from app.db.database import execute_query

logger = logging.getLogger(__name__)

AI_SERVICE_ENV_PATH = Path(__file__).resolve().parents[3] / "ai-service" / ".env"
load_dotenv(AI_SERVICE_ENV_PATH)

# ── Provider → 默认 base URL（config 缺失时的兜底） ──────

_FALLBACK_BASE_URLS: Dict[str, str] = {
    "deepseek": "https://api.deepseek.com/v1",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4",
}

_PROVIDER_ENV_PREFIX: Dict[str, str] = {
    "deepseek": "SUMMARY_LLM",
    "zhipu": "EVIDENCE_LLM",
}


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("true", "1", "yes", "on")


def _is_configured_api_key(value: str) -> bool:
    return bool(value and value.strip() and value.strip() != "YOUR_API_KEY")


class LLMService:
    """多 Provider LLM 调用服务。

    Provider API keys are never read from system_config.
    """

    def __init__(self) -> None:
        self._config_cache: Optional[Dict[str, Any]] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl_seconds = 60

    # ── 配置读取 ──────────────────────────────────────

    def _read_config(self) -> Dict[str, Any]:
        """Read non-sensitive AI config rows for legacy admin views."""
        now = datetime.now()
        if (
            self._config_cache is not None
            and self._cache_time is not None
            and (now - self._cache_time).total_seconds() < self._cache_ttl_seconds
        ):
            return self._config_cache

        try:
            rows = execute_query(
                "SELECT config_key, config_value, config_type FROM system_config WHERE config_key LIKE %s",
                ["ai.%"],
            )
        except Exception:
            rows = []

        cfg: Dict[str, Any] = {}
        for r in (rows or []):
            k = r["config_key"]
            v = r["config_value"]
            t = r.get("config_type", "string")
            if t == "boolean":
                cfg[k] = v in ("true", "True", "1", "yes")
            elif t == "int":
                cfg[k] = int(v) if v else 0
            elif t == "float":
                cfg[k] = float(v) if v else 0.0
            else:
                cfg[k] = v or ""

        self._config_cache = cfg
        self._cache_time = now
        return cfg

    def _get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get provider config from ai-service/.env only."""
        defaults = get_provider_defaults(provider)  # type: ignore[arg-type]
        prefix = _PROVIDER_ENV_PREFIX.get(provider, "EVIDENCE_LLM")
        return {
            "provider": os.getenv(f"{prefix}_PROVIDER", provider) or provider,
            "enabled": _env_bool(f"{prefix}_ENABLED", "false"),
            "api_key": os.getenv(f"{prefix}_API_KEY", "") or "",
            "base_url": os.getenv(
                f"{prefix}_BASE_URL",
                defaults.get("base_url", _FALLBACK_BASE_URLS.get(provider, "")),
            ),
            "model": os.getenv(f"{prefix}_MODEL", defaults.get("model", "")),
            "timeout": int(os.getenv(f"{prefix}_TIMEOUT", defaults.get("timeout", "60"))),
        }

    def is_available(self, provider: str = "zhipu") -> bool:
        """检查指定 provider 是否可用。"""
        pcfg = self._get_provider_config(provider)
        return bool(pcfg["enabled"] and _is_configured_api_key(pcfg["api_key"]))

    # ── Chat Completion ───────────────────────────────

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: Optional[str] = None,
        provider: str = "zhipu",
        timeout: Optional[float] = None,
    ) -> tuple[Optional[str], Optional[str]]:
        """调用 LLM chat completion。

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            temperature: 温度参数
            max_tokens: 最大 token 数
            model: 模型名（不传则用 provider 默认模型）
            provider: LLM 提供商 "deepseek" | "zhipu"
            timeout: 超时（秒），不传则用 provider 默认值

        Returns:
            (response_text, error_message)
        """
        pcfg = self._get_provider_config(provider)
        if not pcfg["enabled"]:
            return None, f"{provider} LLM disabled in ai-service/.env"

        api_key = pcfg["api_key"]
        if not _is_configured_api_key(api_key):
            return None, f"未配置 {provider} API Key"

        model_name = model or pcfg["model"]
        timeout_val = timeout or pcfg["timeout"]
        base_url = pcfg["base_url"].rstrip("/")
        url = f"{base_url}/chat/completions"

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        logger.info(
            "🤖 [LLM/%s] Calling %s model=%s temp=%.2f timeout=%ss",
            provider.upper(), url, model_name, temperature, timeout_val,
        )

        try:
            async with httpx.AsyncClient(timeout=timeout_val, follow_redirects=True) as client:
                resp = await client.post(url, json=payload, headers=headers)
                logger.info("📡 [LLM/%s] HTTP %s (%d bytes)", provider.upper(), resp.status_code, len(resp.content))

                if resp.status_code != 200:
                    error_detail = resp.text[:500]
                    logger.error("❌ [LLM/%s] API error: %s — %s", provider.upper(), resp.status_code, error_detail)
                    return None, f"{provider} API 错误 ({resp.status_code}): {error_detail}"

                body = resp.json()
                choices = body.get("choices", [])
                if not choices:
                    return None, f"{provider} 返回空响应"

                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    return None, f"{provider} 返回空内容"

                usage = body.get("usage", {})
                logger.info(
                    "✅ [LLM/%s] 成功 — tokens: prompt=%s, completion=%s, total=%s",
                    provider.upper(),
                    usage.get("prompt_tokens", "?"),
                    usage.get("completion_tokens", "?"),
                    usage.get("total_tokens", "?"),
                )

                return content, None

        except httpx.TimeoutException:
            return None, f"{provider} 调用超时 ({timeout_val}s)"
        except httpx.ConnectError as e:
            return None, f"{provider} 连接失败: {str(e)}"
        except Exception as e:
            logger.exception("❌ [LLM/%s] 未知异常", provider.upper())
            return None, f"{provider} 调用异常: {type(e).__name__}: {str(e)}"

    # ── JSON 模式 Chat ─────────────────────────────────

    async def chat_json(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        model: Optional[str] = None,
        provider: str = "zhipu",
        timeout: Optional[float] = None,
    ) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """调用 LLM 并解析 JSON 响应。

        Args:
            provider: LLM 提供商 "deepseek" | "zhipu"

        Returns:
            (parsed_dict, error_message)
        """
        json_system = f"{system_prompt}\n\n【重要】你必须严格按照要求返回合法的 JSON 格式，不要包含任何其他文字。"
        text, error = await self.chat(
            system_prompt=json_system,
            user_message=user_message,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            provider=provider,
            timeout=timeout,
        )
        if error:
            return None, error
        if not text:
            return None, f"{provider} 返回空响应"

        # 尝试提取 JSON
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text), None
        except json.JSONDecodeError:
            match = _re.search(r'\{.*\}', text, _re.DOTALL)
            if match:
                try:
                    return json.loads(match.group()), None
                except json.JSONDecodeError:
                    pass
            return None, f"{provider} 返回无法解析为 JSON: {text[:200]}"


# ── 全局单例 ──────────────────────────────────────────

llm_service = LLMService()
