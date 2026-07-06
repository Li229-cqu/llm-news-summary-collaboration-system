#!/usr/bin/env python3
"""Local smoke test for ai-service LLM configuration."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.services.llm_client import call_summary_llm, mask_api_key


def _configured(value: str) -> bool:
    return bool(value and value.strip() and value.strip() != "YOUR_API_KEY")


async def main() -> bool:
    print("Summary LLM configuration")
    print(f"  SUMMARY_LLM_ENABLED: {settings.summary_llm_enabled}")
    print(f"  SUMMARY_LLM_PROVIDER: {settings.summary_llm_provider}")
    print(f"  SUMMARY_LLM_API_KEY: {mask_api_key(settings.summary_llm_api_key)}")
    print(f"  SUMMARY_LLM_BASE_URL: {settings.summary_llm_base_url}")
    print(f"  SUMMARY_LLM_MODEL: {settings.summary_llm_model}")
    print()

    if not settings.summary_llm_enabled:
        print("SUMMARY_LLM_ENABLED=false; real model call is disabled.")
        return False
    if not _configured(settings.summary_llm_api_key):
        print("SUMMARY_LLM_API_KEY is not configured in ai-service/.env.")
        return False

    response = await call_summary_llm(
        [{"role": "user", "content": "用一句话概括：人工智能正在推动新闻内容生产方式变革。"}],
        max_tokens=128,
    )
    print(response)
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
