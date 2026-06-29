#!/usr/bin/env python3
"""
智谱 GLM LLM 客户端测试脚本。

用途：本地测试 llm_client.py 的功能，验证 API Key 配置和模型调用是否正常。

使用方式：
    python scripts/test_llm_client.py

注意：
    该脚本仅用于开发测试，不影响服务启动。
    运行前请确保：
    1. 已安装依赖：pip install -r requirements.txt
    2. 已在 ai-service/.env 中配置 LLM_API_KEY
"""

import sys
import os
from pathlib import Path

# 添加项目路径，使得可以导入 app 模块
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.services.llm_client import call_llm, mask_api_key
from app.core.config import settings


def main():
    """运行测试。"""
    print("=" * 60)
    print("智谱 GLM LLM 客户端测试")
    print("=" * 60)
    print()

    # 1. 打印配置信息（脱敏 API Key）
    print("📋 当前配置信息：")
    print(f"  LLM_ENABLED: {settings.llm_enabled}")
    print(f"  LLM_PROVIDER: {settings.llm_provider}")
    print(f"  LLM_API_KEY: {mask_api_key(settings.llm_api_key)}")
    print(f"  LLM_BASE_URL: {settings.llm_base_url}")
    print(f"  LLM_MODEL: {settings.llm_model}")
    print(f"  LLM_TIMEOUT: {settings.llm_timeout}")
    print(f"  LLM_TEMPERATURE: {settings.llm_temperature}")
    print(f"  LLM_MAX_TOKENS: {settings.llm_max_tokens}")
    print(f"  LLM_THINKING_TYPE: {settings.llm_thinking_type}")
    print()

    # 2. 检查 API Key 是否配置
    if not settings.llm_api_key or settings.llm_api_key.strip() == "":
        print("❌ 错误：API Key 未配置")
        print()
        print("请按以下步骤配置：")
        print("  1. 复制 ai-service/.env.example 为 ai-service/.env")
        print("  2. 在 ai-service/.env 中填入真实的智谱 API Key")
        print("     LLM_API_KEY=sk-你的真实APIKey")
        print("  3. 重新运行本脚本")
        print()
        return False

    # 3. 检查 LLM_ENABLED 状态
    if not settings.llm_enabled:
        print("⚠️  警告：LLM_ENABLED 为 false，需要启用才能调用模型")
        print()
        print("如要测试，请修改 ai-service/.env：")
        print("  LLM_ENABLED=true")
        print()
        return False

    # 4. 调用 LLM
    print("🚀 开始调用智谱 GLM...")
    print()

    test_message = "请用一句话概括：人工智能正在推动新闻内容生产方式变革。"
    messages = [{"role": "user", "content": test_message}]

    try:
        response = call_llm(messages)

        print("✅ 调用成功！")
        print()
        print("📝 模型回复：")
        print("-" * 60)
        print(response)
        print("-" * 60)
        print()
        return True

    except ValueError as e:
        print(f"❌ 参数错误：{str(e)}")
        print()
        return False
    except Exception as e:
        print(f"❌ 调用失败：{type(e).__name__}")
        print(f"   详情：{str(e)}")
        print()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
