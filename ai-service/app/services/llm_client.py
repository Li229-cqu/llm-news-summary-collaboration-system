""""""

from __future__ import annotations

from typing import List, Optional, Union
from dataclasses import dataclass

import logging
from openai import AsyncOpenAI, APIError

from app.core.config import settings, LLMConfig

logger = logging.getLogger(__name__)


def mask_api_key(api_key: str) -> str:
    if not api_key or len(api_key) == 0:
        return "未配置"

    if len(api_key) <= 10:
        return "sk-****"

    return f"{api_key[:6]}{'*' * (len(api_key) - 10)}{api_key[-4:]}"


def build_zhipu_extra_body() -> dict:
    extra_body = {}

    if settings.llm_thinking_type in ("enabled", "disabled"):
        pass

    return extra_body


async def call_llm_with_config(
    llm_config: LLMConfig,
    messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    if not llm_config.api_key or llm_config.api_key.strip() == "":
        raise ValueError(
            f"未配置 {llm_config.provider} API Key，请检查 ai-service/.env 配置"
        )

    if not messages or len(messages) == 0:
        raise ValueError("调用 LLM 的消息列表不能为空")

    logger.info(
        f"🚀 [REAL API] 调用 {llm_config.provider} LLM: "
        f"model={llm_config.model}, "
        f"api_key={mask_api_key(llm_config.api_key)}"
    )

    try:
        client = AsyncOpenAI(
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            timeout=llm_config.timeout,
        )

        actual_temperature = temperature if temperature is not None else llm_config.temperature
        actual_max_tokens = max_tokens if max_tokens is not None else llm_config.max_tokens

        request_kwargs = {
            "model": llm_config.model,
            "messages": messages,
            "temperature": actual_temperature,
            "max_tokens": actual_max_tokens,
        }

        if llm_config.provider.lower() == "zhipu":
            extra_body = build_zhipu_extra_body()
            if extra_body:
                request_kwargs["extra_body"] = extra_body

        response = await client.chat.completions.create(**request_kwargs)

        content = response.choices[0].message.content

        if not content or content.strip() == "":
            raise ValueError(f"{llm_config.provider} 模型返回的内容为空")

        logger.info(f"✅ [REAL API] {llm_config.provider} LLM 调用成功，返回内容长度：{len(content)} 字符")
        return content

    except APIError as e:
        logger.error(f"❌ [REAL API] {llm_config.provider} LLM 调用失败: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"❌ [REAL API] {llm_config.provider} LLM 参数错误: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"❌ [REAL API] {llm_config.provider} LLM 调用异常: {type(e).__name__}: {str(e)}")
        raise


async def call_llm_with_config_stream(
    llm_config: LLMConfig,
    messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
):
    """流式调用 LLM，逐 token yield。"""
    if not llm_config.api_key or llm_config.api_key.strip() == "":
        raise ValueError(
            f"未配置 {llm_config.provider} API Key，请检查 ai-service/.env 配置"
        )

    if not messages or len(messages) == 0:
        raise ValueError("调用 LLM 的消息列表不能为空")

    logger.info(
        f"🚀 [STREAM API] 调用 {llm_config.provider} LLM (流式): "
        f"model={llm_config.model}, "
        f"api_key={mask_api_key(llm_config.api_key)}"
    )

    try:
        client = AsyncOpenAI(
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            timeout=llm_config.timeout,
        )

        actual_temperature = temperature if temperature is not None else llm_config.temperature
        actual_max_tokens = max_tokens if max_tokens is not None else llm_config.max_tokens

        request_kwargs = {
            "model": llm_config.model,
            "messages": messages,
            "temperature": actual_temperature,
            "max_tokens": actual_max_tokens,
            "stream": True,
        }

        if llm_config.provider.lower() == "zhipu":
            extra_body = build_zhipu_extra_body()
            if extra_body:
                request_kwargs["extra_body"] = extra_body

        stream = await client.chat.completions.create(**request_kwargs)

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content is not None:
                yield delta.content

        logger.info(f"✅ [STREAM API] {llm_config.provider} LLM 流式调用完成")

    except APIError as e:
        logger.error(f"❌ [STREAM API] {llm_config.provider} LLM 流式调用失败: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"❌ [STREAM API] {llm_config.provider} LLM 参数错误: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"❌ [STREAM API] {llm_config.provider} LLM 调用异常: {type(e).__name__}: {str(e)}")
        raise


async def call_summary_llm_stream(
    messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
):
    """流式调用 Summary LLM，逐 token yield。"""
    async for token in call_llm_with_config_stream(settings.summary_llm_config, messages, temperature, max_tokens):
        yield token


async def call_summary_llm(
    messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    return await call_llm_with_config(settings.summary_llm_config, messages, temperature, max_tokens)


async def call_evidence_llm(
    messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    return await call_llm_with_config(settings.evidence_llm_config, messages, temperature, max_tokens)


async def call_llm(
    messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    if not settings.summary_llm_api_key or settings.summary_llm_api_key.strip() == "":
        raise ValueError(
            "未配置生成类 AI API Key，请检查 ai-service/.env 中的 SUMMARY_LLM_API_KEY"
        )

    if not messages or len(messages) == 0:
        raise ValueError("调用 LLM 的消息列表不能为空")

    logger.info(
        f"调用生成类 LLM: "
        f"provider={settings.summary_llm_provider}, "
        f"model={settings.summary_llm_model}, "
        f"api_key={mask_api_key(settings.summary_llm_api_key)}"
    )

    try:
        client = AsyncOpenAI(
            api_key=settings.summary_llm_api_key,
            base_url=settings.summary_llm_base_url,
            timeout=settings.summary_llm_timeout,
        )

        actual_temperature = temperature if temperature is not None else settings.summary_llm_temperature
        actual_max_tokens = max_tokens if max_tokens is not None else settings.summary_llm_max_tokens

        request_kwargs = {
            "model": settings.summary_llm_model,
            "messages": messages,
            "temperature": actual_temperature,
            "max_tokens": actual_max_tokens,
        }

        extra_body = build_zhipu_extra_body()
        if extra_body:
            request_kwargs["extra_body"] = extra_body

        response = await client.chat.completions.create(**request_kwargs)

        content = response.choices[0].message.content

        if not content or content.strip() == "":
            raise ValueError("智谱模型返回的内容为空")

        logger.info(f"智谱 LLM 调用成功，返回内容长度：{len(content)} 字符")
        return content

    except APIError as e:
        logger.error(f"智谱 LLM 调用失败: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"智谱 LLM 参数错误: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"智谱 LLM 调用异常: {type(e).__name__}: {str(e)}")
        raise
