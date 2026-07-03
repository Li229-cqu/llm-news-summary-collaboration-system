"""LLM Provider Policy — 双模型职责分层策略（Phase 1）。

规则：
- DeepSeek = 生成类任务（"出题老师"）：关键词提取、六要素识别、标题摘要生成、话题匹配
- Zhipu   = 审核类任务（"审题老师"）：时间线适配、一致性检查、编辑建议生成

Provider 选择优先级：
1. Pipeline 步骤显式指定 provider
2. llm_service.chat(provider="deepseek|zhipu") 参数
3. 默认 fallback → zhipu（历史兼容）
"""

from __future__ import annotations

from typing import Dict, Literal, Optional

ProviderName = Literal["deepseek", "zhipu"]

# ── 步骤 → Provider 映射 ───────────────────────────

STEP_PROVIDER_MAP: Dict[str, ProviderName] = {
    "clean":              "deepseek",   # 文本清洗（本地处理，不调 LLM）
    "extract_keywords":   "deepseek",   # 关键词提取 → 生成类
    "extract_elements":   "deepseek",   # 六要素识别 → 生成类
    "generate_title_summary": "deepseek",  # 标题摘要生成 → 生成类（出题）
    "match_topic":        "deepseek",   # 话题匹配 → 生成类
    "judge_timeline":     "zhipu",      # 时间线适配 → 审核类
    "check_consistency":  "zhipu",      # 一致性检查 → 审核类（审题）
    "edit_suggestions":   "zhipu",      # 编辑建议 → 审核类
}

# ── Provider 默认配置 ──────────────────────────────

PROVIDER_DEFAULTS: Dict[str, Dict[str, str]] = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "timeout": "120",
        "description": "DeepSeek — 生成类任务（出题老师）",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
        "timeout": "60",
        "description": "Zhipu GLM — 审核类任务（审题老师）",
    },
}


def get_step_provider(step_name: str) -> ProviderName:
    """根据步骤名返回对应的 LLM provider。

    Args:
        step_name: 步骤标识（如 'extract_keywords', 'check_consistency'）

    Returns:
        'deepseek' | 'zhipu'
    """
    return STEP_PROVIDER_MAP.get(step_name, "zhipu")


def get_provider_defaults(provider: ProviderName) -> Dict[str, str]:
    """获取 provider 的默认配置（base_url, model, timeout）。"""
    return PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["zhipu"])
