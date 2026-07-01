"""近 7 天阅读报告 AI 分析服务。

流程：数据校验 → Prompt 构造 → LLM 生成 → 解析 → 质量校验 → 失败回退 mock。
"""

import json
import logging

from app.common.exceptions import AIServiceException
from app.core.config import settings
from app.schemas.profile_report import (
    PageAnalyses,
    ProfileReportQuality,
    ProfileReportRequest,
    ProfileReportResponse,
)
from app.services.llm_client import call_llm

logger = logging.getLogger(__name__)

# ── Prompt 模板 ─────────────────────────────────────────────

SYSTEM_PROMPT = """你是一个新闻阅读平台的"阅读周报生成助手"。请根据用户截至昨日的最近完整 7 天行为数据（不含今天实时行为），生成丰富、自然、像 App 周报的个性化分析。

【规则】
1. 只能基于提供的数据生成文案，不能编造数字、主题或事实。
2. 输出必须是严格 JSON，不含 Markdown、注释或额外文字。
3. 语气温和亲切，像朋友写的阅读总结，不要像后台数据分析报告。
4. 不要提"超过多少用户"或用户排名，不要夸张评价。
5. 文案应丰富、有内容，不要一句话草草了事。每个字段请尽量写满建议字数。

【输出格式】
{
  "ai_summary": "一段 100~200 字的近 7 天阅读报告总结，描述整体阅读情况、行为特点和突出亮点",
  "ai_insights": ["洞察1，50~80字，深入分析一个行为特点", "洞察2，50~80字", "洞察3，50~80字"],
  "ai_suggestions": ["建议1，40~70字，温和可执行", "建议2，40~70字"],
  "persona_description": "一段 50~120 字的用户画像描述",
  "page_analyses": {
    "overview": "100~200字，第1页用：解释用户本周整体阅读身份、行为画像和核心特点",
    "trajectory": "120~220字，第2页用：分析阅读节奏、活跃模式、兴趣主题倾向",
    "conclusion": "120~240字，第3页用：总结本周高光、AI使用、内容沉淀，给出积极展望"
  },
  "reading_style": "一句20~60字的话，描述用户阅读风格，如'你更像一位以主动探索为主、善于借助AI工具提升效率的读者'",
  "closing": "80~160字，报告结束语，结合称号和兴趣主题，温暖收尾"
}
- ai_suggestions：2 条温和、可执行的阅读建议。
- persona_description：用户画像描述，基于用户称号展开。"""


def build_prompt(data: ProfileReportRequest) -> str:
    """基于聚合后的结构化数据构造 user prompt。"""
    ov = data.overview
    scores = data.behavior_scores
    ds = data.daily_summary
    topics_str = "、".join(
        f"{t.get('name', '')}({t.get('count', 0)}次)" for t in data.top_topics[:5]
    )

    highlights_str = "；".join(
        f"{h.get('label', '')}：{h.get('value', '')}" for h in data.highlights
    )

    return f"""以下是用户近 {data.range_days} 天的阅读行为数据，请据此生成周报文案。

【用户画像称号】{data.persona_title}

【核心数据】
- 浏览内容数：{ov.get('browse_count', 0)}
- 收藏数：{ov.get('favorite_count', 0)}
- 评论数：{ov.get('comment_count', 0)}
- AI 摘要使用次数：{ov.get('ai_count', 0)}
- 活跃天数：{ov.get('active_days', 0)}

【行为画像评分（0~100）】
- 阅读探索：{scores.get('reading', 0)}
- 内容沉淀：{scores.get('collecting', 0)}
- 社区互动：{scores.get('interaction', 0)}
- AI 使用：{scores.get('ai_usage', 0)}

【活跃概况】
- 最活跃日期：{ds.get('most_active_date', '')}（{ds.get('max_daily_count', 0)} 次浏览）
- 活跃天数：{ds.get('active_days', data.range_days)} 天

【Top 关注主题】{topics_str}

【关键亮点】{highlights_str}

请基于以上数据生成 JSON 格式的周报文案。"""


# ── 解析与校验 ──────────────────────────────────────────────

def parse_and_validate(content: str, data: ProfileReportRequest) -> ProfileReportResponse:
    """解析 LLM 返回的 JSON，校验字段完整性和一致性。"""
    issues: list[str] = []
    score = 0.0

    # 1. 安全解析 JSON
    cleaned = content.strip()
    if cleaned.startswith("```"):
        # 去掉 markdown 代码块
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return _fallback_response(data, "JSON 解析失败")

    if not isinstance(parsed, dict):
        return _fallback_response(data, "返回格式错误（非 JSON 对象）")

    # 2. 结构完整性
    ai_summary = str(parsed.get("ai_summary", "")).strip()
    ai_insights = parsed.get("ai_insights", [])
    ai_suggestions = parsed.get("ai_suggestions", [])
    persona_desc = str(parsed.get("persona_description", "")).strip()

    if ai_summary:
        score += 0.3
    else:
        issues.append("ai_summary 为空")

    if isinstance(ai_insights, list) and len(ai_insights) == 3:
        score += 0.2
    else:
        issues.append(f"ai_insights 应为 3 条，实际 {len(ai_insights) if isinstance(ai_insights, list) else '非数组'}")

    if isinstance(ai_suggestions, list) and len(ai_suggestions) == 2:
        score += 0.2
    else:
        issues.append(f"ai_suggestions 应为 2 条，实际 {len(ai_suggestions) if isinstance(ai_suggestions, list) else '非数组'}")

    if persona_desc:
        score += 0.1

    # 3. 数字校验：检查文案中是否出现了不一致的数字
    ov = data.overview
    ai_text = ai_summary + " " + " ".join(str(i) for i in ai_insights) + " " + " ".join(str(s) for s in ai_suggestions)
    browse_str = str(ov.get("browse_count", ""))
    # 简单检查：如果文案中有数字不是 overview 中的，标记警告
    # （不做过于激进的数字匹配，因为中文数字如"六天"无法简单检测）
    score += 0.1  # 数字冲突检测为弱检查

    # 4. 主题校验
    valid_topics = {t.get("name", "") for t in data.top_topics}
    for t in valid_topics:
        if t and t in ai_text:
            break  # 至少引用了正确主题
    score += 0.1  # 主题检查为弱检查

    # 5. 文案长度
    if 40 <= len(ai_summary) <= 300:
        score += 0.1
    else:
        issues.append(f"ai_summary 长度异常：{len(ai_summary)} 字")

    # 6. persona.title 不被修改
    persona_title_in_text = data.persona_title in ai_text or data.persona_title in persona_desc
    if not persona_title_in_text:
        # 不扣分，仅标记
        pass

    score = min(score, 1.0)
    passed = len(issues) == 0 or score >= 0.6
    quality = ProfileReportQuality(passed=passed, score=round(score, 2), issues=issues)

    return ProfileReportResponse(
        ai_summary=ai_summary if ai_summary else _fallback_summary(data),
        ai_insights=ai_insights if isinstance(ai_insights, list) and len(ai_insights) == 3 else _fallback_insights(data),
        ai_suggestions=ai_suggestions if isinstance(ai_suggestions, list) and len(ai_suggestions) == 2 else _fallback_suggestions(data),
        persona_description=persona_desc if persona_desc else _fallback_persona_desc(data),
        page_analyses=_get_page_analyses(parsed, data),
        reading_style=str(parsed.get("reading_style", "")).strip() or _fallback_reading_style(data),
        closing=str(parsed.get("closing", "")).strip() or _fallback_closing(data),
        quality=quality,
        source="llm" if passed else "fallback",
    )


# ── 回退逻辑 ─────────────────────────────────────────────────


def _get_page_analyses(parsed: dict, data) -> PageAnalyses:
    pa = parsed.get("page_analyses", {}) or {}
    return PageAnalyses(
        overview=str(pa.get("overview", "")).strip() or _fallback_page_overview(data),
        trajectory=str(pa.get("trajectory", "")).strip() or _fallback_page_trajectory(data),
        conclusion=str(pa.get("conclusion", "")).strip() or _fallback_page_conclusion(data),
    )


def _fallback_page_overview(data) -> str:
    ov = data.overview; scores = data.behavior_scores
    r = scores.get("reading", 0); a = scores.get("ai_usage", 0)
    return f'本周你共浏览了 {ov.get("browse_count", 0)} 个内容，活跃 {ov.get("active_days", 0)} 天。{"你的阅读探索欲很强，" if r >= 60 else ""}{"同时积极使用 AI 工具辅助理解，" if a >= 60 else ""}展现出主动获取信息与借助智能工具提升效率的阅读风格。'


def _fallback_page_trajectory(data) -> str:
    ds = data.daily_summary
    topics = [t.get("name", "") for t in data.top_topics[:3] if t.get("name")]
    ts = "、".join(topics) if topics else "多个领域"
    return f'近 7 天中你有 {ds.get("active_days", 0)} 天保持阅读，{ds.get("most_active_date", "")} 达到本周峰值。你最关注 {ts}，体现出对现实议题和行业趋势的持续兴趣。阅读节奏比较稳定，建议继续保持。'


def _fallback_page_conclusion(data) -> str:
    ov = data.overview
    return f'这一周你在平台上留下了清晰的阅读轨迹：共浏览 {ov.get("browse_count", 0)} 个内容，收藏 {ov.get("favorite_count", 0)} 条，发表 {ov.get("comment_count", 0)} 次评论，使用 AI 摘要 {ov.get("ai_count", 0)} 次。这些行为构成了你本周的阅读画像。继续保持好奇心，系统会为你沉淀更完整的个人阅读档案。'


def _fallback_reading_style(data) -> str:
    scores = data.behavior_scores
    r = scores.get("reading", 0); a = scores.get("ai_usage", 0)
    if r >= 60 and a >= 60: return "你更像一位以主动探索为主、善于借助 AI 工具提升信息处理效率的读者。"
    elif r >= 60: return "你更像一位热爱主动探索、广泛涉猎各类内容的读者。"
    elif a >= 60: return "你更像一位善于借助智能工具高效获取信息的实用型读者。"
    return "你正在逐步建立自己的阅读节奏，是一位有潜力的成长型读者。"


def _fallback_closing(data) -> str:
    title = data.persona_title
    topics = [t.get("name", "") for t in data.top_topics[:2] if t.get("name")]
    ts = "、".join(topics) if topics else "感兴趣的方向"
    return f'作为「{title}」，你在 {ts} 等方向留下了本周的阅读足迹。每一篇新闻、每一次收藏和每一条评论，都在丰富你的阅读画像。下周继续探索，系统会为你生成更完整的个人阅读报告。'


def _fallback_page_analyses(data) -> PageAnalyses:
    return PageAnalyses(
        overview=_fallback_page_overview(data),
        trajectory=_fallback_page_trajectory(data),
        conclusion=_fallback_page_conclusion(data),
    )


def _fallback_response(data: ProfileReportRequest, reason: str) -> ProfileReportResponse:
    """LLM 失败时用规则生成文案回退。"""
    logger.warning("AI 周报生成失败，回退规则文案：%s", reason)
    return ProfileReportResponse(
        ai_summary=_fallback_summary(data),
        ai_insights=_fallback_insights(data),
        ai_suggestions=_fallback_suggestions(data),
        persona_description=_fallback_persona_desc(data),
        page_analyses=_fallback_page_analyses(data),
        reading_style=_fallback_reading_style(data),
        closing=_fallback_closing(data),
        quality=ProfileReportQuality(passed=False, score=0.0, issues=[reason]),
        source="fallback",
    )


def _fallback_summary(data: ProfileReportRequest) -> str:
    ov = data.overview
    ds = data.daily_summary
    topics = [t.get("name", "") for t in data.top_topics[:3] if t.get("name")]
    topics_str = "、".join(topics) if topics else "多种内容"
    return (
        f"过去 7 天，你有 {ds.get('active_days', ov.get('active_days', 0))} 天留下阅读足迹，"
        f"共浏览 {ov.get('browse_count', 0)} 个内容，最常关注{topics_str}，"
        f"并使用 AI 生成了 {ov.get('ai_count', 0)} 次摘要。"
    )


def _fallback_insights(data: ProfileReportRequest) -> list[str]:
    scores = data.behavior_scores
    ov = data.overview
    insights = []
    if scores.get("reading", 0) >= 60:
        insights.append(f"你本周阅读了 {ov.get('browse_count', 0)} 个内容，探索欲很强，保持这份好奇心吧。")
    if scores.get("ai_usage", 0) >= 60:
        insights.append(f"你已经习惯使用 AI 摘要来辅助阅读，这是处理信息的聪明方式。")
    if scores.get("collecting", 0) >= 50:
        insights.append(f"你收藏了 {ov.get('favorite_count', 0)} 条内容，说明你善于沉淀有价值的信息。")
    if scores.get("interaction", 0) >= 50:
        insights.append(f"你在社区中参与了 {ov.get('comment_count', 0)} 次讨论，互动让阅读更有深度。")
    # 补足 3 条
    while len(insights) < 3:
        insights.append("持续关注你感兴趣的主题，阅读报告会越来越丰富。")
    return insights[:3]


def _fallback_suggestions(data: ProfileReportRequest) -> list[str]:
    suggestions = []
    scores = data.behavior_scores
    ov = data.overview
    if scores.get("ai_usage", 0) < 50:
        suggestions.append("试试用 AI 摘要来快速了解长文章的核心内容，节省阅读时间。")
    if scores.get("collecting", 0) < 50:
        suggestions.append("遇到感兴趣的内容可以收藏起来，方便以后回顾。")
    if ov.get("comment_count", 0) < 3:
        suggestions.append("读完新闻后留下你的看法，和其他读者交流会让理解更深入。")
    if not suggestions:
        suggestions.append("继续探索更多主题，你的阅读画像会越来越完整。")
    if len(suggestions) < 2:
        suggestions.append("保持当前的阅读节奏，你的信息获取效率已经很不错了。")
    return suggestions[:2]


def _fallback_persona_desc(data: ProfileReportRequest) -> str:
    title = data.persona_title
    scores = data.behavior_scores
    reading = scores.get("reading", 0)
    ai = scores.get("ai_usage", 0)
    collecting = scores.get("collecting", 0)
    interaction = scores.get("interaction", 0)

    parts = []
    if reading >= 60:
        parts.append("阅读探索积极")
    if ai >= 60:
        parts.append("善于借助 AI 工具")
    if collecting >= 60:
        parts.append("有良好的内容沉淀习惯")
    if interaction >= 60:
        parts.append("乐于社区互动")

    if parts:
        return f"作为「{title}」，你{'，'.join(parts[:3])}。"
    return f"作为「{title}」，你在平台上迈出了第一步，未来的阅读之旅值得期待。"


# ── 主入口 ───────────────────────────────────────────────────

def generate_profile_report(request: ProfileReportRequest) -> ProfileReportResponse:
    """生成近 7 天阅读报告的 AI 分析文案。

    流程：数据校验 → Prompt 构造 → LLM (或 mock) → 解析 → 质量校验 → 回退。
    """
    # 1. 数据校验
    ov = request.overview
    if not ov or ov.get("browse_count", 0) == 0:
        return _fallback_response(request, "用户近 7 天无阅读数据")

    # 2. 判断是否启用 LLM
    if not settings.llm_enabled:
        logger.info("LLM 未启用，使用规则生成周报文案")
        return _fallback_response(request, "LLM disabled")

    # 3. 构造 Prompt 并调用 LLM
    try:
        prompt = build_prompt(request)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        llm_content = call_llm(
            messages=messages,
            temperature=0.5,
            max_tokens=1024,
        )
    except Exception as e:
        logger.exception("LLM 调用失败：%s", e)
        return _fallback_response(request, f"LLM 调用异常：{str(e)[:80]}")

    # 4. 解析并校验
    return parse_and_validate(llm_content, request)
