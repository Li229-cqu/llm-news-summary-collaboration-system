""""""

from __future__ import annotations

from typing import List, Optional, Union


import logging
from openai import OpenAI, APIError

from app.core.config import settings

logger = logging.getLogger(__name__)


def mask_api_key(api_key: str) -> str:
    """
    脱敏显示 API Key，避免日志中暴露完整 Key。

    示例：
    - 输入: "sk-1234567890abcdefghij"
    - 输出: "sk-123456****j"
    """
    if not api_key or len(api_key) == 0:
        return "未配置"

    if len(api_key) <= 10:
        return "sk-****"

    # 显示前 6 位和后 4 位，中间用星号代替
    return f"{api_key[:6]}{'*' * (len(api_key) - 10)}{api_key[-4:]}"


def build_zhipu_extra_body() -> dict:
    """
    构造智谱扩展参数。

    thinking 参数作为智谱扩展配置预留，若接口不兼容则不传递。
    当前版本先返回空 dict，保留后续扩展入口。
    """
    extra_body = {}

    # TODO: 后续根据智谱 OpenAI 兼容接口的最新文档确认
    # thinking 参数的具体字段和传递方式
    if settings.llm_thinking_type in ("enabled", "disabled"):
        # 暂不强制传递，避免接口不兼容导致请求失败
        # 可参考：https://open.bigmodel.cn/api/paas/v4/chat/completions
        pass

    return extra_body


def call_llm(
    messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """
    调用智谱 GLM-4-Flash 模型。

    参数：
    - messages: 消息列表，每条消息为 {"role": "user"|"assistant"|"system", "content": str}
    - temperature: 温度参数（可选，不传则使用配置的默认值）
    - max_tokens: 最大 Token 数（可选，不传则使用配置的默认值）

    返回：
    - 模型生成的文本内容

    异常：
    - ValueError: 配置不完整、输入为空、模型返回为空
    - APIError: 模型调用失败
    """
    # 检查 API Key 是否配置
    if not settings.llm_api_key or settings.llm_api_key.strip() == "":
        raise ValueError(
            "未配置智谱 API Key，请检查 ai-service/.env 中的 LLM_API_KEY"
        )

    # 检查 messages 是否为空
    if not messages or len(messages) == 0:
        raise ValueError("调用 LLM 的消息列表不能为空")

    # 记录调用信息（脱敏 API Key）
    logger.info(
        f"调用智谱 LLM: "
        f"provider={settings.llm_provider}, "
        f"model={settings.llm_model}, "
        f"api_key={mask_api_key(settings.llm_api_key)}"
    )

    try:
        # 使用 OpenAI 兼容方式初始化客户端
        client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout,
        )

        # 使用实际参数或配置的默认值
        actual_temperature = temperature if temperature is not None else settings.llm_temperature
        actual_max_tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens

        # 构造请求参数
        request_kwargs = {
            "model": settings.llm_model,
            "messages": messages,
            "temperature": actual_temperature,
            "max_tokens": actual_max_tokens,
        }

        # 添加智谱扩展参数（如有）
        extra_body = build_zhipu_extra_body()
        if extra_body:
            request_kwargs["extra_body"] = extra_body

        # 调用 API
        response = client.chat.completions.create(**request_kwargs)

        # 提取内容
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
