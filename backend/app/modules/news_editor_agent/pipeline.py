"""News Editor Agent — 流水线引擎（Phase 2：真实 AI 接入 + DAG 并行）。

架构：
- STEP_REGISTRY: 8 个步骤函数的注册表
- 每个步骤：async def x_step(ctx: AgentContext) -> StepResult
- run_pipeline(): DAG 编排，使用 asyncio.gather 并行执行独立步骤

DAG 执行顺序：
    Step1 (clean)
       ↓
    [Step2 (keywords) ∥ Step3 (elements)]   ← asyncio.gather
       ↓
    Step4 (generate)
       ↓
    [Step5 (match_topic) ∥ Step6 (judge_timeline)]  ← asyncio.gather
       ↓
    Step7 (check)
       ↓
    Step8 (edit_suggestions)

AI 服务调用（真实）：
- POST /ai/extract-elements     → Step 2, 3
- POST /ai/generate-title-summary → Step 4
- POST /ai/check-consistency    → Step 7
- POST /ai/match-topic          → Step 5（如不可用则 mock fallback）
- POST /ai/judge-timeline-fit   → Step 6（如不可用则 mock fallback）
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core.llm_provider_policy import get_step_provider
from app.modules.news_editor_agent.fallback_nlp import (
    split_sentences,
    extract_keywords_fallback,
    extract_elements_fallback,
    generate_title_summary_fallback,
    match_topic_fallback,
    judge_timeline_fallback,
    check_consistency_fallback,
    edit_suggestions_fallback,
)
from app.modules.news_editor_agent.schema import AgentContext, StepMeta, StepResult
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# 步骤元数据
# ═══════════════════════════════════════════════════════════

STEP_META: Dict[str, Dict[str, str]] = {
    "clean":              {"label": "正文清洗",       "order": 1},
    "extract_keywords":   {"label": "关键词提取",     "order": 2},
    "extract_elements":   {"label": "六要素识别",     "order": 3},
    "generate_title_summary": {"label": "标题摘要生成", "order": 4},
    "match_topic":        {"label": "话题匹配",       "order": 5},
    "judge_timeline":     {"label": "时间线适配",     "order": 6},
    "check_consistency":  {"label": "一致性检查",     "order": 7},
    "edit_suggestions":   {"label": "编辑建议生成",   "order": 8},
}


def _step_label(name: str) -> str:
    return STEP_META.get(name, {}).get("label", name)


def _step_order(name: str) -> int:
    return STEP_META.get(name, {}).get("order", 0)


# ═══════════════════════════════════════════════════════════
# Step 1: 正文清洗（本地处理，无 AI 调用）
# ═══════════════════════════════════════════════════════════

def _clean_text(text: str) -> Tuple[str, Dict[str, Any]]:
    """本地文本清洗（纯规则，无 LLM 调用）。

    清洗步骤：
    1. 统一换行 + 去除 HTML/Markdown 标记
    2. 删除来源/编辑/记者署名行
    3. 删除重复句子
    4. 删除广告/免责声明/URL
    5. 合并短句
    6. 规范化空白
    """
    original_length = len(text)
    removals: List[str] = []

    cleaned = text

    # ── 1. 统一换行 ──────────────────────────────────────
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # ── 2. 去除 HTML/Markdown 标记 ──────────────────────
    # HTML 标签
    html_before = len(cleaned)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    if len(cleaned) < html_before:
        removals.append("HTML 标签")

    # Markdown 图片/链接（保留文字）
    cleaned = re.sub(r"!\[.*?\]\(.*?\)", "", cleaned)   # 图片
    cleaned = re.sub(r"\[([^\]]*)\]\(.*?\)", r"\1", cleaned)  # 链接保留文字

    # ── 3. 删除来源/编辑元信息行 ────────────────────────
    meta_patterns = [
        (r"(?:责任编辑|责编|编辑|记者|通讯员|作者)[：:]\s*[^\n]*", "编辑署名"),
        (r"(?:来源|出处|转载自|文章来源)[：:]\s*[^\n]*", "来源标注"),
        (r"（(?:责任编辑|责编|编辑|记者)[^）]*）", "括号署名"),
        (r"【(?:责任编辑|责编|来源|转载)[^】]*】", "方括号标注"),
        (r"^\s*(?:本文|此文|文章|稿件)(?:来源|来自|转自|转载).*$", "稿件来源行"),
    ]
    for pattern, label in meta_patterns:
        before = len(cleaned)
        matches = re.findall(pattern, cleaned, re.IGNORECASE | re.MULTILINE)
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
        if matches and len(cleaned) < before:
            removals.append(label)

    # ── 4. 删除广告/免责声明 ────────────────────────────
    ad_patterns = [
        (r"广告[：:].*", "广告语"),
        (r"免责声明[：:].*", "免责声明"),
        (r"【广告】.*", "广告标记"),
        (r"^\s*扫码.*$", "扫码提示"),
        (r"^\s*关注.*(?:公众号|微信|微博).*$", "关注提示"),
    ]
    for pattern, label in ad_patterns:
        before = len(cleaned)
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
        if len(cleaned) < before:
            removals.append(label)

    # ── 5. 删除 URL ────────────────────────────────────
    url_before = len(cleaned)
    cleaned = re.sub(r"https?://\S+", "", cleaned)
    if len(cleaned) < url_before:
        removals.append("URL 链接")

    # ── 6. 删除纯符号/数字行 ────────────────────────────
    cleaned = re.sub(r"^\s*[\d\W_]+\s*$", "", cleaned, flags=re.MULTILINE)

    # ── 7. 删除重复句子 ────────────────────────────────
    sentences = re.split(r"(?<=[。！？.!?])\s*", cleaned)
    seen: set = set()
    unique_sentences: List[str] = []
    dup_count = 0
    for s in sentences:
        normalized = re.sub(r"\s+", "", s)
        if normalized and normalized in seen:
            dup_count += 1
            continue
        if normalized:
            seen.add(normalized)
        unique_sentences.append(s)
    if dup_count > 0:
        removals.append(f"重复句子 ×{dup_count}")
    cleaned = "".join(unique_sentences)

    # ── 8. 合并过短的相邻句（< 20 字的句子合并到前一句） ──
    sentences = re.split(r"(?<=[。！？.!?])\s*", cleaned)
    merged: List[str] = []
    merge_count = 0
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(s) < 20 and merged:
            merged[-1] = merged[-1].rstrip() + s
            merge_count += 1
        else:
            merged.append(s)
    if merge_count > 0:
        removals.append(f"合并短句 ×{merge_count}")
    cleaned = "".join(merged)

    # ── 9. 规范化空白 ──────────────────────────────────
    cleaned = re.sub(r"[ \t]+", " ", cleaned)              # 多空格 → 单空格
    cleaned = re.sub(r"^[ \t]+", "", cleaned, flags=re.MULTILINE)  # 行首空格
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)            # 多空行 → 双空行
    cleaned = cleaned.strip()

    cleaned_length = len(cleaned)
    reduction_pct = round((1 - cleaned_length / max(original_length, 1)) * 100, 1)

    # 生成清洗前后对比文本（截取关键差异区域）
    diff_preview = _build_diff_preview(text, cleaned)

    return cleaned, {
        "original_length": original_length,
        "cleaned_length": cleaned_length,
        "reduction_pct": reduction_pct,
        "compression_ratio": round(cleaned_length / max(original_length, 1), 3),
        "removed_noise": removals,
        "diff_preview": diff_preview,
    }


def _build_diff_preview(original: str, cleaned: str) -> Dict[str, Any]:
    """构建清洗前后对比 — 生成带删除标注的全文。

    返回 annotated_text: 清洗后全文，被删除部分用（删除：xxx）标注。
    deleted_segments: 被删除的片段列表。
    """
    import difflib

    # 按行做 diff
    orig_lines = original.splitlines(keepends=True)
    clean_lines = cleaned.splitlines(keepends=True)

    diff = list(difflib.unified_diff(orig_lines, clean_lines, n=0))
    deleted_segments: List[str] = []

    annotated = cleaned  # 默认直接用清洗后文本

    # 用 SequenceMatcher 找出被删除的文本段
    matcher = difflib.SequenceMatcher(None, original, cleaned)
    deletions: List[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "delete":
            seg = original[i1:i2].strip()
            if seg and len(seg) > 2:  # 过滤太短的（标点/空格）
                deletions.append(seg)
        elif tag == "replace":
            old = original[i1:i2].strip()
            if old and len(old) > 2:
                deletions.append(old)

    # 构建带标注的清洗后文本
    # 在每个删除点附近插入标注
    annotated_parts: List[str] = []
    last_j = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("delete", "replace"):
            deleted_text = original[i1:i2].strip()
            if deleted_text and len(deleted_text) > 2 and deleted_text not in (" ", "\n", "  "):
                seg = f"（删除：{deleted_text[:60]}{'…' if len(deleted_text) > 60 else ''}）"
                deleted_segments.append({"text": deleted_text[:100], "position": i1})
        if tag in ("equal", "replace", "insert"):
            if j2 > last_j:
                annotated_parts.append(cleaned[last_j:j2])
            last_j = j2
    if last_j < len(cleaned):
        annotated_parts.append(cleaned[last_j:])

    annotated_text = "".join(annotated_parts) if annotated_parts else cleaned

    # 生成统计摘要
    change_summary = f"共删除 {len(deleted_segments)} 处冗余内容" if deleted_segments else "清洗后无明显变化"

    return {
        "annotated_text": annotated_text[:2000],  # 带标注的全文（限制2000字）
        "deleted_segments": deleted_segments[:20],  # 最多20条
        "change_summary": change_summary,
    }


async def clean_step(ctx: AgentContext) -> StepResult:
    """Step 1: 本地文本清洗。"""
    input_snapshot = {"raw_text": ctx.raw_text[:200]}
    t0 = time.time()
    cleaned, stats = _clean_text(ctx.raw_text)
    elapsed_ms = int((time.time() - t0) * 1000)

    ctx.cleaned_text = cleaned
    return StepResult(
        step="clean",
        status="completed",
        input=input_snapshot,
        output={"cleaned_text": cleaned[:500], **stats},
        time_ms=elapsed_ms,
        meta=StepMeta(provider="local", model="regex"),
    )


# ═══════════════════════════════════════════════════════════
# Step 2: 关键词提取（调用 AI extract-elements）
# ═══════════════════════════════════════════════════════════

async def extract_keywords_step(ctx: AgentContext) -> StepResult:
    """Step 2: 调用 LLM 提取关键词。"""
    text = ctx.cleaned_text or ctx.raw_text
    input_snapshot = {"text": text[:200]}
    params = ctx.pipeline_params or {}
    temperature = params.get("temperature", 0.3)
    model = params.get("model") or None
    provider = get_step_provider("extract_keywords")
    provider_model = model or llm_service._get_provider_config(provider)["model"]

    t0 = time.time()

    # ── 真实 LLM 调用 ─────────────────────────────────
    if llm_service.is_available(provider):
        data, error = await llm_service.chat_json(
            system_prompt="你是一个专业的新闻关键词提取助手。从新闻文本中提取最重要的关键词，返回 JSON 格式。",
            user_message=f"""请从以下新闻文本中提取 5-10 个最重要的关键词，按重要性排序。

对于每个关键词，提供：
- word: 关键词
- weight: 重要性权重 (0-1)
- type: 类型（核心主题/技术突破/市场表现/产业配套/行业指标 等）

新闻文本：
{text[:3000]}

请严格返回 JSON 格式：
{{"keywords": [{{"word": "...", "weight": 0.95, "type": "..."}}, ...], "total_count": 5}}""",
            temperature=temperature,
            model=provider_model,
            provider=provider,
        )
        elapsed_ms = int((time.time() - t0) * 1000)

        if data and not error:
            keywords = data.get("keywords", [])
            ctx.keywords = [k.get("word", k) if isinstance(k, dict) else k for k in keywords]
            return StepResult(
                step="extract_keywords",
                status="completed",
                input=input_snapshot,
                output={"keywords": keywords, "total_count": len(keywords), "llm": True},
                time_ms=elapsed_ms,
                meta=StepMeta(provider=provider, model=provider_model, latency_ms=elapsed_ms),
            )
        logger.warning("⚠️ [extract_keywords] %s 失败，使用 mock: %s", provider, error)
    else:
        logger.info("ℹ️ [extract_keywords] %s 未配置/未启用，使用 mock", provider)

    # ── NLP fallback ──────────────────────────────────
    elapsed_ms = int((time.time() - t0) * 1000)
    keywords_fb = extract_keywords_fallback(text)
    ctx.keywords = [k.get("word", k) if isinstance(k, dict) else k for k in keywords_fb]
    return StepResult(
        step="extract_keywords",
        status="completed",
        input=input_snapshot,
        output={"keywords": keywords_fb, "total_count": len(keywords_fb), "llm": False},
        time_ms=elapsed_ms,
        meta=StepMeta(provider="nlp", model="fallback_rule", latency_ms=elapsed_ms),
    )


# ═══════════════════════════════════════════════════════════
# Step 3: 六要素识别（调用 AI extract-elements）
# ═══════════════════════════════════════════════════════════

async def extract_elements_step(ctx: AgentContext) -> StepResult:
    """Step 3: 调用 LLM 识别新闻六要素（5W1H）。

    Phase 1 升级：
    - 使用 DeepSeek provider
    - 输出为空时自动 retry 1 次
    - 确保返回合法 JSON（非空、非 string）
    """
    text = ctx.cleaned_text or ctx.raw_text
    input_snapshot = {"text": text[:200]}
    params = ctx.pipeline_params or {}
    provider = get_step_provider("extract_elements")
    provider_model = params.get("model") or llm_service._get_provider_config(provider)["model"]
    temperature = params.get("temperature", 0.3)

    t0 = time.time()
    data = None
    error = None

    # ── 真实 LLM 调用（含 retry） ─────────────────────
    if llm_service.is_available(provider):
        for attempt in range(2):  # 最多 2 次尝试
            data, error = await llm_service.chat_json(
                system_prompt=("你是一个专业的新闻分析助手。从新闻文本中提取六要素（5W1H），返回 JSON 格式。每个要素必须填写，如果原文未提及则填未知。"),
                user_message=f"""请从以下新闻文本中提取新闻六要素（5W1H），必须全部填写，不能为空：

- who: 涉及的人物/组织/机构
- what: 核心事件是什么
- when: 事件发生时间
- where: 事件发生地点
- why: 事件原因/背景
- how: 如何发生/进展

新闻文本：
{text[:3000]}

请严格返回 JSON 格式（每个字段都必须有值）：
{{"news_elements": {{"who": "...", "what": "...", "when": "...", "where": "...", "why": "...", "how": "..."}}, "confidence": 0.9}}""",
                temperature=temperature,
                model=provider_model,
                provider=provider,
                timeout=120.0,
            )

            if error:
                logger.warning("⚠️ [extract_elements] %s 尝试 %d/2 失败: %s", provider, attempt + 1, error)
                if attempt == 0:
                    continue  # retry
                break

            # 校验输出非空
            if data:
                elements = data.get("news_elements", data)
                if elements and isinstance(elements, dict):
                    # 检查是否有 at least one non-empty value
                    has_value = any(
                        v and str(v).strip() and str(v).strip() != "未知"
                        for v in elements.values()
                    )
                    if has_value:
                        break  # success
                    else:
                        logger.warning("⚠️ [extract_elements] 返回全为空/未知，retry...")
                        if attempt == 0:
                            continue  # retry
                else:
                    logger.warning("⚠️ [extract_elements] news_elements 为空或非 dict，retry...")
                    if attempt == 0:
                        continue  # retry
                    data = None
            else:
                logger.warning("⚠️ [extract_elements] 返回 data 为空，retry...")
                if attempt == 0:
                    continue  # retry

        elapsed_ms = int((time.time() - t0) * 1000)

        if data and not error:
            elements = data.get("news_elements", data)
            ctx.news_elements = elements
            logger.info("✅ [extract_elements] %s 成功: who=%s, what=%s", provider,
                        str(elements.get("who", ""))[:30], str(elements.get("what", ""))[:50])
            return StepResult(
                step="extract_elements",
                status="completed",
                input=input_snapshot,
                output={"news_elements": elements, "llm": True},
                time_ms=elapsed_ms,
                meta=StepMeta(provider=provider, model=provider_model, latency_ms=elapsed_ms),
            )
        logger.warning("⚠️ [extract_elements] %s 全部尝试失败，使用 mock: %s", provider, error)
    else:
        logger.info("ℹ️ [extract_elements] %s 未配置/未启用，使用 mock", provider)

    # ── NLP fallback ──────────────────────────────────
    elapsed_ms = int((time.time() - t0) * 1000)
    elements_fb = extract_elements_fallback(text)
    ctx.news_elements = elements_fb.get("news_elements", elements_fb)
    return StepResult(
        step="extract_elements",
        status="completed",
        input=input_snapshot,
        output=elements_fb,
        time_ms=elapsed_ms,
        meta=StepMeta(provider="nlp", model="fallback_rule", latency_ms=elapsed_ms),
    )


# ═══════════════════════════════════════════════════════════
# Step 4: 标题摘要生成（调用 AI generate-title-summary）
# ═══════════════════════════════════════════════════════════

async def generate_step(ctx: AgentContext) -> StepResult:
    """Step 4: 调用 LLM 生成标题与摘要。

    严格遵循侧边栏参数：
    - title_count: 候选标题数量 (1-5)
    - title_style: 标题风格（客观新闻型/吸引点击型/简洁概括型）
    - summary_type: 摘要类型（generate 生成式 / extract 抽取式）
    - summary_style: 摘要风格（简明扼要/客观正式/通俗易懂）
    - summary_length: 长度（short/long/both）— long = short 的 2-4 倍
    """
    text = ctx.cleaned_text or ctx.raw_text
    params = ctx.pipeline_params or {}
    title_count = int(params.get("title_count", 3))
    temperature = params.get("temperature", 0.7)
    title_style = params.get("title_style", "客观新闻型")
    summary_type = params.get("summary_type", "generate")
    summary_style = params.get("summary_style", "简明扼要")
    summary_length = params.get("summary_length", "both")
    model = params.get("model") or None
    provider = get_step_provider("generate_title_summary")
    provider_model = model or llm_service._get_provider_config(provider)["model"]

    # ── 根据参数构建精确指令 ─────────────────────────────

    TITLE_STYLE_INSTRUCTIONS = {
        "客观新闻型": "标题必须客观中立，使用陈述句，避免感叹号、问号和主观评价。事实在前，观点在后。",
        "吸引点击型": "标题应有吸引力，可使用设问、数字对比、悬念等手法，但不可做标题党。适当使用冒号分隔。",
        "简洁概括型": "标题必须极简，控制在15字以内，直接点出核心事实，删除一切修饰语。",
    }
    title_instruction = TITLE_STYLE_INSTRUCTIONS.get(title_style, "标题应客观准确。")

    if summary_type == "extract":
        type_instruction = "摘要方式：抽取式——直接从原文中抽取关键句并拼接，不要改写或生成新句子。保留原文措辞。"
    else:
        type_instruction = "摘要方式：生成式——理解原文后用自己的语言重新组织摘要，保持信息完整但不照抄原文。"

    STYLE_INSTRUCTIONS = {
        "简明扼要": "摘要风格：言简意赅，删除冗余修饰，每句话承载一个核心信息点。",
        "客观正式": "摘要风格：使用正式客观的新闻语言，避免口语化和情绪化表达。使用第三人称。",
        "通俗易懂": "摘要风格：通俗易懂，避免专业术语和复杂句式。即使普通读者也能理解。",
    }
    style_instruction = STYLE_INSTRUCTIONS.get(summary_style, "摘要应简洁清晰。")

    if summary_length == "short":
        length_instruction = "只生成 summary_short（50-100 字），不需要 summary_long。"
        length_hint = '"summary_short": "简短摘要（50-100字）"'
    elif summary_length == "long":
        length_instruction = "只生成 summary_long（200-400 字，是短摘要长度的 2-4 倍），不需要 summary_short。"
        length_hint = '"summary_long": "详细摘要（200-400字，是短摘要的2-4倍长度）"'
    else:
        length_instruction = "同时生成 summary_short（50-100 字）和 summary_long（200-400 字，必须比 short 长 2-4 倍）。long 字数必须 >= short 字数 * 2。"
        length_hint = '"summary_short": "简短摘要（50-100字）", "summary_long": "详细摘要（200-400字，至少是short的2倍长度）"'

    input_snapshot = {
        "text": text[:300],
        "keywords": ctx.keywords[:3] if ctx.keywords else [],
        "elements_summary": ctx.news_elements.get("what", "") if ctx.news_elements else "",
        "title_count": title_count,
        "title_style": title_style,
        "summary_type": summary_type,
        "summary_length": summary_length,
    }

    t0 = time.time()

    if llm_service.is_available(provider):
        kw_text = ", ".join(ctx.keywords[:5]) if ctx.keywords else "无"
        elements = ctx.news_elements or {}
        data, error = await llm_service.chat_json(
            system_prompt=f"""你是一个专业的新闻编辑。你的任务是根据新闻文本生成标题和摘要。

【标题要求】
{title_instruction}
必须生成恰好 {title_count} 个候选标题。

【摘要要求】
{type_instruction}
{style_instruction}
{length_instruction}

【重要】你必须严格返回合法的 JSON 格式，不要包含任何其他文字。""",
            user_message=f"""请根据以下新闻文本生成标题和摘要。

参考信息：
- 关键词：{kw_text}
- 六要素：{json.dumps(elements, ensure_ascii=False)}

新闻文本：
{text[:3000]}

请生成：
1. candidate_titles: 恰好 {title_count} 个候选标题
2. {length_instruction}

请严格返回 JSON 格式：
{{{{candidate_titles: ["标题1", ...], {length_hint}}}}}""",
            temperature=temperature,
            max_tokens=2048,
            model=provider_model,
            provider=provider,
            timeout=120.0,
        )
        elapsed_ms = int((time.time() - t0) * 1000)

        if data and not error:
            titles = data.get("candidate_titles", [])
            title = titles[0] if titles else ""
            summary = data.get("summary_short", "")
            ctx.title = title
            ctx.summary = summary
            ctx.summary_long = data.get("summary_long", "")
            return StepResult(
                step="generate_title_summary",
                status="completed",
                input=input_snapshot,
                output={
                    "candidate_titles": titles,
                    "summary_short": summary,
                    "summary_long": data.get("summary_long", ""),
                    "llm": True,
                },
                time_ms=elapsed_ms,
                meta=StepMeta(provider=provider, model=provider_model, latency_ms=elapsed_ms),
            )
        logger.warning("⚠️ [generate] %s 失败，使用 mock: %s", provider, error)
    else:
        logger.info("ℹ️ [generate] %s 未配置/未启用，使用 mock", provider)

    # ── NLP fallback ──────────────────────────────────
    elapsed_ms = int((time.time() - t0) * 1000)
    gen_fb = generate_title_summary_fallback(
        text, params=params,
        keywords=ctx.keywords if ctx.keywords else None,
        elements=ctx.news_elements if ctx.news_elements else None,
    )
    titles = gen_fb.get("candidate_titles", [])
    ctx.title = titles[0] if titles else ""
    ctx.summary = gen_fb.get("summary_short", "")
    ctx.summary_long = gen_fb.get("summary_long", "")
    return StepResult(
        step="generate_title_summary",
        status="completed",
        input=input_snapshot,
        output=gen_fb,
        time_ms=elapsed_ms,
        meta=StepMeta(provider="nlp", model="fallback_rule", latency_ms=elapsed_ms),
    )


# ═══════════════════════════════════════════════════════════
# Step 5: 话题匹配（调用 AI match-topic，暂无则 mock）
# ═══════════════════════════════════════════════════════════

async def match_topic_step(ctx: AgentContext) -> StepResult:
    """Step 5: 调用 LLM 匹配新闻话题分类。"""
    text = ctx.cleaned_text or ctx.raw_text
    input_snapshot = {
        "text": text[:200],
        "keywords": ctx.keywords[:3] if ctx.keywords else [],
        "title": ctx.title or "",
    }

    t0 = time.time()

    provider = get_step_provider("match_topic")
    provider_model = llm_service._get_provider_config(provider)["model"]

    if llm_service.is_available(provider):
        kw_text = ", ".join(ctx.keywords[:5]) if ctx.keywords else "无"
        data, error = await llm_service.chat_json(
            system_prompt="你是一个新闻话题分类专家。根据新闻内容匹配最合适的话题分类。",
            user_message=f"""请分析以下新闻，确定话题分类。

参考信息：
- 标题：{ctx.title or '无'}
- 关键词：{kw_text}
- 事件概要：{ctx.news_elements.get('what', '无') if ctx.news_elements else '无'}

新闻文本：
{text[:2000]}

请确定：
1. primary_topic: 主要话题分类
2. secondary_topics: 2-3 个次要话题（字符串数组）
3. confidence: 匹配置信度 (0-1)
4. topic_category: 话题大类（科技/产业/政策/财经/社会/国际/体育/娱乐）

请严格返回 JSON 格式：
{{"primary_topic": "...", "secondary_topics": ["...", "..."], "confidence": 0.9, "topic_category": "科技/产业"}}""",
            temperature=0.3,
            provider=provider,
            model=provider_model,
        )
        elapsed_ms = int((time.time() - t0) * 1000)

        if data and not error:
            ctx.topic = data
            return StepResult(
                step="match_topic",
                status="completed",
                input=input_snapshot,
                output={**data, "llm": True},
                time_ms=elapsed_ms,
                meta=StepMeta(provider=provider, model=provider_model, latency_ms=elapsed_ms),
            )
        logger.warning("⚠️ [match_topic] %s 失败，使用 mock: %s", provider, error)
    else:
        logger.info("ℹ️ [match_topic] %s 未配置/未启用，使用 mock", provider)

    elapsed_ms = int((time.time() - t0) * 1000)
    topic_fb = match_topic_fallback(text, keywords=ctx.keywords if ctx.keywords else None)
    ctx.topic = topic_fb
    return StepResult(
        step="match_topic",
        status="completed",
        input=input_snapshot,
        output={**topic_fb, "llm": False},
        time_ms=elapsed_ms,
        meta=StepMeta(provider="nlp", model="fallback_rule", latency_ms=elapsed_ms),
    )


# ═══════════════════════════════════════════════════════════
# Step 6: 时间线适配（调用 AI judge-timeline-fit，暂无则 mock）
# ═══════════════════════════════════════════════════════════

async def judge_timeline_step(ctx: AgentContext) -> StepResult:
    """Step 6: 调用 LLM 判断新闻时效性与时间线适配。"""
    text = ctx.cleaned_text or ctx.raw_text
    input_snapshot = {
        "text": (ctx.cleaned_text or ctx.raw_text)[:200],
        "when": ctx.news_elements.get("when", "") if ctx.news_elements else "",
    }

    t0 = time.time()

    provider = get_step_provider("judge_timeline")
    provider_model = llm_service._get_provider_config(provider)["model"]

    if llm_service.is_available(provider):
        when = ctx.news_elements.get("when", "未知") if ctx.news_elements else "未知"
        data, error = await llm_service.chat_json(
            system_prompt="你是一个新闻时效性分析专家。判断新闻的时效性和推荐发布位置。",
            user_message=f"""请分析以下新闻的时效性。

参考信息：
- 标题：{ctx.title or '无'}
- 事件时间：{when}
- 事件概要：{ctx.news_elements.get('what', '无') if ctx.news_elements else '无'}

新闻文本：
{(ctx.cleaned_text or ctx.raw_text)[:2000]}

请判断：
1. is_timely: 是否具有时效性 (true/false)
2. time_sensitivity: 时效敏感度（高/中/低）
3. recommended_position: 推荐发布位置（头条/要闻区/科技频道/一般新闻）
4. expiration_hours: 预计失效时间（小时数，如 48）
5. reason: 判断理由

请严格返回 JSON 格式：
{{"is_timely": true, "time_sensitivity": "高", "recommended_position": "头条/要闻区", "expiration_hours": 48, "reason": "..."}}""",
            temperature=0.3,
            provider=provider,
            model=provider_model,
        )
        elapsed_ms = int((time.time() - t0) * 1000)

        if data and not error:
            ctx.timeline = data
            return StepResult(
                step="judge_timeline",
                status="completed",
                input=input_snapshot,
                output={**data, "llm": True},
                time_ms=elapsed_ms,
                meta=StepMeta(provider=provider, model=provider_model, latency_ms=elapsed_ms),
            )
        logger.warning("⚠️ [judge_timeline] %s 失败，使用 mock: %s", provider, error)
    else:
        logger.info("ℹ️ [judge_timeline] %s 未配置/未启用，使用 mock", provider)

    elapsed_ms = int((time.time() - t0) * 1000)
    timeline_fb = judge_timeline_fallback(text)
    ctx.timeline = timeline_fb
    return StepResult(
        step="judge_timeline",
        status="completed",
        input=input_snapshot,
        output={**timeline_fb, "llm": False},
        time_ms=elapsed_ms,
        meta=StepMeta(provider="nlp", model="fallback_rule", latency_ms=elapsed_ms),
    )


# ═══════════════════════════════════════════════════════════
# Step 7: 一致性检查（调用 AI check-consistency）
# ═══════════════════════════════════════════════════════════

async def check_step(ctx: AgentContext) -> StepResult:
    """Step 7: 调用 Zhipu 进行一致性检查 + 原文对齐分析。

    输出增强：
    - similarity_map: 每句摘要 ↔ 原文句子对齐（score + 幻觉检测）
    - highlight_segments: 原文关键段落标色（覆盖/偏离/未覆盖）
    """
    text = ctx.cleaned_text or ctx.raw_text
    title = ctx.title or ""
    summary = ctx.summary or ""
    summary_long = ctx.summary_long or ""

    input_snapshot = {
        "source_text_len": len(text),
        "title": title,
        "summary": summary[:100],
    }

    t0 = time.time()

    provider = get_step_provider("check_consistency")
    provider_model = llm_service._get_provider_config(provider)["model"]
    if llm_service.is_available(provider):
        data, error = await llm_service.chat_json(
            system_prompt="""你是一个新闻事实核查与AI对齐检测专家。你的任务是：

1. 检查AI生成的标题/摘要与原文的一致性
2. 逐句分析摘要是否能在原文中找到依据
3. 判断每句摘要是「匹配原文」「偏离原文」还是「AI幻觉」
4. 标注原文中哪些段落被AI覆盖、哪些被忽略

判定标准：
- match（匹配）: 摘要内容可在原文找到对应句子，score >= 0.7
- drift（偏离）: 摘要意思大致对但措辞/细节有改动，score 0.4-0.7
- hallucination（幻觉）: 摘要内容在原文中完全找不到依据，score < 0.4""",
            user_message=f"""请对以下AI生成内容进行事实核查和对齐分析。

【AI 生成的标题】
{title}

【AI 生成的短摘要】
{summary}

【AI 生成的长摘要】
{summary_long or '（未生成长摘要）'}

【原文（前3000字）】
{text[:3000]}

请输出：
1. risk_level: 综合风险等级（low/medium/high）
2. risk_label: 风险标签（低风险/中等风险/高风险）
3. check_items: 检查项数组 [{{"name": "...", "status": "pass/warn/fail", "message": "..."}}]
4. suggestions: 改进建议（字符串数组）
5. similarity_map: 逐句对齐分析数组 [{{"summary_sentence": "摘要中的一句话", "source_sentence": "原文中对应的句子或'无对应'", "score": 0.85, "type": "match/drift/hallucination", "reason": "判断理由"}}]
6. highlight_segments: 原文关键段落标注 [{{"text_range": "原文中某段文字(前50字)", "score": 0.9, "covered": true/false}}]

请严格返回 JSON：
{{"risk_level": "low", "risk_label": "低风险", "check_items": [...], "suggestions": [...], "similarity_map": [{{"summary_sentence": "...", "source_sentence": "...", "score": 0.87, "type": "match", "reason": "..."}}], "highlight_segments": [{{"text_range": "...", "score": 0.92, "covered": true}}]}}""",
            temperature=0.15,
            max_tokens=3072,
            provider=provider,
            model=provider_model,
            timeout=90.0,
        )
        elapsed_ms = int((time.time() - t0) * 1000)

        if data and not error:
            ctx.consistency = data
            return StepResult(
                step="check_consistency",
                status="completed",
                input=input_snapshot,
                output={**data, "llm": True},
                time_ms=elapsed_ms,
                meta=StepMeta(provider=provider, model=provider_model, latency_ms=elapsed_ms),
            )
        logger.warning("⚠️ [check] %s 失败，使用 mock: %s", provider, error)
    else:
        logger.info("ℹ️ [check] %s 未配置/未启用，使用 mock", provider)

    elapsed_ms = int((time.time() - t0) * 1000)
    consistency_fb = check_consistency_fallback(
        text, (ctx.summary or "") + " " + (ctx.summary_long or "")
    )
    ctx.consistency = consistency_fb
    return StepResult(
        step="check_consistency",
        status="completed",
        input=input_snapshot,
        output={**consistency_fb, "llm": False},
        time_ms=elapsed_ms,
        meta=StepMeta(provider="nlp", model="fallback_rule", latency_ms=elapsed_ms),
    )


# ═══════════════════════════════════════════════════════════
# Step 8: 编辑建议生成（LLM 汇总 context，暂无独立端点则 mock）
# ═══════════════════════════════════════════════════════════

# ── 建议类型归一化映射表 ──────────────────────────────
_EDIT_TYPE_NORMALIZE_MAP: Dict[str, str] = {
    # 英文 → 中文
    "title": "标题优化", "headline": "标题优化", "heading": "标题优化",
    "summary": "摘要优化", "abstract": "摘要优化", "digest": "摘要优化",
    "fact": "事实核查", "fact check": "事实核查", "fact_check": "事实核查",
    "consistency": "事实核查", "evidence": "事实核查", "verification": "事实核查",
    "element": "要素补充", "5w1h": "要素补充", "who": "要素补充",
    "what": "要素补充", "when": "要素补充", "where": "要素补充",
    "why": "要素补充", "how": "要素补充", "six_elements": "要素补充",
    "structure": "结构建议", "format": "结构建议", "layout": "结构建议",
    "quality": "质量提醒", "risk": "质量提醒", "warning": "质量提醒",
    "publish": "发布建议", "release": "发布建议", "deploy": "发布建议",
    "keyword": "要素补充", "keywords": "要素补充",
    # 中文变体 → 统一
    "标题": "标题优化", "标题建议": "标题优化", "标题修改": "标题优化",
    "摘要": "摘要优化", "内容摘要": "摘要优化", "摘要修改": "摘要优化",
    "事实": "事实核查", "核查": "事实核查", "一致性": "事实核查",
    "要素": "要素补充", "六要素": "要素补充",
    "结构": "结构建议", "格式": "结构建议",
    "质量": "质量提醒", "风险": "质量提醒",
    "发布": "发布建议",
    "优化": "质量提醒",
    "建议": "质量提醒",
}

# 关键词 → 兜底类型映射（按 detail/reason 中的关键词判断）
_TYPE_KEYWORD_HINTS: list = [
    (["标题", "title", "headline"], "标题优化"),
    (["摘要", "summary", "abstract"], "摘要优化"),
    (["事实", "核查", "fact", "consistency", "一致"], "事实核查"),
    (["要素", "5w1h", "element", "要素"], "要素补充"),
    (["结构", "structure", "format", "分段", "段落"], "结构建议"),
    (["质量", "风险", "quality", "risk", "警告"], "质量提醒"),
    (["发布", "publish", "release", "上线"], "发布建议"),
]


def _normalize_edit_type(raw_type: str, detail: str = "", reason: str = "") -> str:
    """将 LLM 返回的建议类型归一化为中文枚举值。"""
    if not raw_type or not raw_type.strip():
        return "质量提醒"

    key = raw_type.strip().lower().rstrip("：:")

    # 1. 精确匹配
    if key in _EDIT_TYPE_NORMALIZE_MAP:
        return _EDIT_TYPE_NORMALIZE_MAP[key]

    # 2. 模糊匹配（包含关系）
    for en, zh in _EDIT_TYPE_NORMALIZE_MAP.items():
        if en in key or key in en:
            return zh

    # 3. 通过 detail + reason 关键词判断
    combined = f"{detail} {reason}".lower()
    for hints, zh in _TYPE_KEYWORD_HINTS:
        for h in hints:
            if h in key or h in combined:
                return zh

    # 4. 兜底
    return "质量提醒"


async def edit_step(ctx: AgentContext) -> StepResult:
    """Step 8: 调用 LLM 综合所有结果生成编辑建议。"""
    input_snapshot = {
        "title": ctx.title or "",
        "summary": (ctx.summary or "")[:100],
        "topic": ctx.topic.get("primary_topic", "") if ctx.topic else "",
        "risk_level": ctx.consistency.get("risk_level", "unknown") if ctx.consistency else "unknown",
    }

    t0 = time.time()

    provider = get_step_provider("edit_suggestions")
    provider_model = llm_service._get_provider_config(provider)["model"]
    if llm_service.is_available(provider):
        data, error = await llm_service.chat_json(
            system_prompt="你是一个资深新闻主编。综合新闻分析结果，给出专业的编辑建议和改进方案。",
            user_message=f"""请综合以下分析结果，给出编辑建议。

【新闻文本】{(ctx.cleaned_text or ctx.raw_text)[:2000]}

【生成标题】{ctx.title or '无'}
【生成摘要】{ctx.summary or '无'}
【关键词】{', '.join(ctx.keywords) if ctx.keywords else '无'}
【话题分类】{json.dumps(ctx.topic or {}, ensure_ascii=False)}
【时效判断】{json.dumps(ctx.timeline or {}, ensure_ascii=False)}
【一致性检查】{json.dumps(ctx.consistency or {}, ensure_ascii=False)}

请给出：
1. suggestions: 编辑建议数组，每项包含 type、priority、detail、reason
   ⚠️ type 必须使用中文，只能从以下枚举中选择：
      标题优化 / 摘要优化 / 事实核查 / 要素补充 / 结构建议 / 质量提醒 / 发布建议
   priority 使用 high / medium / low
2. overall_score: 综合评分 (0-100)
3. ready_to_publish: 是否可以直接发布 (true/false)

请严格返回 JSON 格式：
{{"suggestions": [{{"type": "标题优化", "priority": "medium", "detail": "具体建议", "reason": "修改理由"}}], "overall_score": 85, "ready_to_publish": true}}""",
            temperature=0.5,
            max_tokens=2048,
            provider=provider,
            model=provider_model,
        )
        elapsed_ms = int((time.time() - t0) * 1000)

        if data and not error:
            # 归一化建议 type 为中文
            suggestions = data.get("suggestions", [])
            if isinstance(suggestions, list):
                for s in suggestions:
                    if isinstance(s, dict):
                        s["type"] = _normalize_edit_type(
                            str(s.get("type", "")),
                            detail=str(s.get("detail", "")),
                            reason=str(s.get("reason", "")),
                        )
            data["suggestions"] = suggestions
            ctx.edit_suggestions = data
            return StepResult(
                step="edit_suggestions",
                status="completed",
                input=input_snapshot,
                output={**data, "llm": True},
                time_ms=elapsed_ms,
                meta=StepMeta(provider=provider, model=provider_model, latency_ms=elapsed_ms),
            )
        logger.warning("⚠️ [edit_suggestions] %s 失败，使用 mock: %s", provider, error)
    else:
        logger.info("ℹ️ [edit_suggestions] %s 未配置/未启用，使用 mock", provider)

    elapsed_ms = int((time.time() - t0) * 1000)
    edit_context = {
        "title": ctx.title or "",
        "summary": ctx.summary or "",
        "summary_long": ctx.summary_long or "",
        "keywords": ctx.keywords if ctx.keywords else [],
        "topic": ctx.topic if ctx.topic else {},
        "consistency": ctx.consistency if ctx.consistency else {},
        "elements": ctx.news_elements if ctx.news_elements else {},
        "text": ctx.cleaned_text or ctx.raw_text,
    }
    edit_fb = edit_suggestions_fallback(edit_context)
    ctx.edit_suggestions = edit_fb
    return StepResult(
        step="edit_suggestions",
        status="completed",
        input=input_snapshot,
        output={**edit_fb, "llm": False},
        time_ms=elapsed_ms,
        meta=StepMeta(provider="nlp", model="fallback_rule", latency_ms=elapsed_ms),
    )


# ═══════════════════════════════════════════════════════════
# STEP_REGISTRY —— 步骤注册表
# ═══════════════════════════════════════════════════════════

STEP_REGISTRY: Dict[str, Callable[[AgentContext], Any]] = {
    "clean": clean_step,
    "extract_keywords": extract_keywords_step,
    "extract_elements": extract_elements_step,
    "generate": generate_step,
    "match_topic": match_topic_step,
    "judge_timeline": judge_timeline_step,
    "check": check_step,
    "edit_suggestions": edit_step,
}


# ═══════════════════════════════════════════════════════════
# DAG 执行引擎
# ═══════════════════════════════════════════════════════════

async def run_pipeline(
    context: AgentContext,
    on_progress: Optional[Callable[[StepResult, int], Any]] = None,
    on_step_event: Optional[Callable[[str, str, int, Optional[Dict[str, Any]]], Any]] = None,
) -> List[StepResult]:
    """按 DAG 拓扑顺序执行全部 8 个步骤。

    DAG 结构：
        Step1 (clean)
           │
           ├──→ Step2 (keywords) ──┐  ← asyncio.gather
           │                        │
           └──→ Step3 (elements) ──┘
                    │
                    ▼
                Step4 (generate)
                    │
           ┌────────┼────────┐
           │        │        │
           ▼        │        ▼
        Step5 (topic) │   Step6 (timeline)   ← asyncio.gather
           │        │        │
           └────────┼────────┘
                    ▼
                Step7 (check)
                    │
                    ▼
                Step8 (edit_suggestions)

    Args:
        context: 贯穿全流程的共享上下文。
        on_progress: 可选，每步完成后回调 async cb(StepResult, order: int)。
        on_step_event: 可选，步骤事件回调 async cb(event_type, step_name, order, extra_data)。
                       event_type: "step_start" | "step_error"
                       用于 SSE 实时推送，不影响流水线执行。

    Returns:
        List[StepResult]: 按执行顺序的 8 个步骤结果。
    """
    results: List[StepResult] = []
    logger.info("🚀 [DAG Pipeline] 开始执行 8 步流水线")

    # ── Phase 1: Step 1 (clean) ───────────────────────────
    logger.info("📍 [DAG] Phase 1/5: Step 1 — 正文清洗")
    if on_step_event:
        await on_step_event("step_start", "clean", 1, None)
    r1 = await STEP_REGISTRY["clean"](context)
    results.append(r1)
    if on_progress:
        await on_progress(r1, 1)
    if r1.status == "failed":
        if on_step_event:
            await on_step_event("step_error", "clean", 1, {"error": "正文清洗失败"})
        return results

    # ── Phase 2: Step 2 ∥ Step 3 (parallel) ──────────────
    logger.info("📍 [DAG] Phase 2/5: Step 2 ∥ Step 3 — 关键词 + 六要素（并行）")
    if on_step_event:
        await on_step_event("step_start", "extract_keywords", 2, None)
        await on_step_event("step_start", "extract_elements", 3, None)
    r2, r3 = await asyncio.gather(
        STEP_REGISTRY["extract_keywords"](context),
        STEP_REGISTRY["extract_elements"](context),
    )
    results.extend([r2, r3])
    if on_progress:
        await on_progress(r2, 2)
        await on_progress(r3, 3)
    if r2.status == "failed" or r3.status == "failed":
        if r2.status == "failed" and on_step_event:
            await on_step_event("step_error", "extract_keywords", 2, {"error": "关键词提取失败"})
        if r3.status == "failed" and on_step_event:
            await on_step_event("step_error", "extract_elements", 3, {"error": "六要素识别失败"})
        return results

    # ── Phase 3: Step 4 (generate) ────────────────────────
    logger.info("📍 [DAG] Phase 3/5: Step 4 — 标题摘要生成")
    if on_step_event:
        await on_step_event("step_start", "generate_title_summary", 4, None)
    r4 = await STEP_REGISTRY["generate"](context)
    results.append(r4)
    if on_progress:
        await on_progress(r4, 4)
    if r4.status == "failed":
        if on_step_event:
            await on_step_event("step_error", "generate_title_summary", 4, {"error": "标题摘要生成失败"})
        return results

    # ── Phase 4: Step 5 ∥ Step 6 (parallel) ──────────────
    logger.info("📍 [DAG] Phase 4/5: Step 5 ∥ Step 6 — 话题匹配 + 时间线适配（并行）")
    if on_step_event:
        await on_step_event("step_start", "match_topic", 5, None)
        await on_step_event("step_start", "judge_timeline", 6, None)
    r5, r6 = await asyncio.gather(
        STEP_REGISTRY["match_topic"](context),
        STEP_REGISTRY["judge_timeline"](context),
    )
    results.extend([r5, r6])
    if on_progress:
        await on_progress(r5, 5)
        await on_progress(r6, 6)
    if r5.status == "failed" or r6.status == "failed":
        if r5.status == "failed" and on_step_event:
            await on_step_event("step_error", "match_topic", 5, {"error": "话题匹配失败"})
        if r6.status == "failed" and on_step_event:
            await on_step_event("step_error", "judge_timeline", 6, {"error": "时间线适配失败"})
        return results

    # ── Phase 5: Step 7 → Step 8 (sequential) ────────────
    logger.info("📍 [DAG] Phase 5/5: Step 7 → Step 8 — 一致性检查 → 编辑建议")
    if on_step_event:
        await on_step_event("step_start", "check_consistency", 7, None)
    r7 = await STEP_REGISTRY["check"](context)
    results.append(r7)
    if on_progress:
        await on_progress(r7, 7)
    if r7.status == "failed":
        if on_step_event:
            await on_step_event("step_error", "check_consistency", 7, {"error": "一致性检查失败"})
        return results

    if on_step_event:
        await on_step_event("step_start", "edit_suggestions", 8, None)
    r8 = await STEP_REGISTRY["edit_suggestions"](context)
    results.append(r8)
    if on_progress:
        await on_progress(r8, 8)

    total_ms = sum(r.time_ms for r in results)
    logger.info("✅ [DAG Pipeline] 全部 8 步完成，总耗时 %s ms", total_ms)
    return results
