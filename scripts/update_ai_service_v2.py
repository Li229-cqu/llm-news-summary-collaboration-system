"""Update ai-service profile_report_service for v2 long-form analysis."""
import re

with open('d:/大三下/实训/project/test/ai-service/app/services/profile_report_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix import
old_imp = 'from app.schemas.profile_report import (\n    ProfileReportQuality,\n    ProfileReportRequest,\n    ProfileReportResponse,\n)'
new_imp = 'from app.schemas.profile_report import (\n    PageAnalyses,\n    ProfileReportQuality,\n    ProfileReportRequest,\n    ProfileReportResponse,\n)'
content = content.replace(old_imp, new_imp)

# 2. Update return in parse_and_validate
old_ret = '''    return ProfileReportResponse(
        ai_summary=ai_summary if ai_summary else _fallback_summary(data),
        ai_insights=ai_insights if isinstance(ai_insights, list) and len(ai_insights) == 3 else _fallback_insights(data),
        ai_suggestions=ai_suggestions if isinstance(ai_suggestions, list) and len(ai_suggestions) == 2 else _fallback_suggestions(data),
        persona_description=persona_desc if persona_desc else _fallback_persona_desc(data),
        quality=quality,
        source="llm" if passed else "fallback",
    )'''
new_ret = '''    return ProfileReportResponse(
        ai_summary=ai_summary if ai_summary else _fallback_summary(data),
        ai_insights=ai_insights if isinstance(ai_insights, list) and len(ai_insights) == 3 else _fallback_insights(data),
        ai_suggestions=ai_suggestions if isinstance(ai_suggestions, list) and len(ai_suggestions) == 2 else _fallback_suggestions(data),
        persona_description=persona_desc if persona_desc else _fallback_persona_desc(data),
        page_analyses=_get_page_analyses(parsed, data),
        reading_style=str(parsed.get("reading_style", "")).strip() or _fallback_reading_style(data),
        closing=str(parsed.get("closing", "")).strip() or _fallback_closing(data),
        quality=quality,
        source="llm" if passed else "fallback",
    )'''
content = content.replace(old_ret, new_ret)

# 3. Update scoring
old_score = '''    if ai_summary:
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

    # 3. 数字校验
    ov = data.overview
    ai_text = ai_summary + " " + " ".join(str(i) for i in ai_insights) + " " + " ".join(str(s) for s in ai_suggestions)
    browse_str = str(ov.get("browse_count", ""))
    score += 0.1

    # 4. 主题校验
    valid_topics = {t.get("name", "") for t in data.top_topics}
    for t in valid_topics:
        if t and t in ai_text:
            break
    score += 0.1

    # 5. 文案长度
    if 40 <= len(ai_summary) <= 300:
        score += 0.1
    else:
        issues.append(f"ai_summary 长度异常：{len(ai_summary)} 字")'''
new_score = '''    if ai_summary: score += 0.2
    else: issues.append("ai_summary 为空")
    if isinstance(ai_insights, list) and len(ai_insights) == 3: score += 0.15
    else: issues.append(f"ai_insights 应为 3 条")
    if isinstance(ai_suggestions, list) and len(ai_suggestions) == 2: score += 0.15
    else: issues.append(f"ai_suggestions 应为 2 条")
    if persona_desc: score += 0.05
    pa_raw = parsed.get("page_analyses", {}) or {}
    if pa_raw.get("overview"): score += 0.1
    else: issues.append("page_analyses.overview 为空")
    if pa_raw.get("trajectory"): score += 0.1
    else: issues.append("page_analyses.trajectory 为空")
    if pa_raw.get("conclusion"): score += 0.1
    else: issues.append("page_analyses.conclusion 为空")
    if str(parsed.get("reading_style", "")).strip(): score += 0.05
    if str(parsed.get("closing", "")).strip(): score += 0.05
    ai_text_all = ai_summary + " " + " ".join(str(i) for i in ai_insights) + " " + " ".join(str(s) for s in ai_suggestions)
    if 80 <= len(ai_summary) <= 400: score += 0.05'''
content = content.replace(old_score, new_score)

# 4. Add helper + fallback functions
helper = '''
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
'''
content = content.replace(
    'def _fallback_response(data: ProfileReportRequest, reason: str) -> ProfileReportResponse:',
    helper + '\n\n' + 'def _fallback_response(data: ProfileReportRequest, reason: str) -> ProfileReportResponse:'
)

# 5. Update fallback_response return
old_fb = '''    return ProfileReportResponse(
        ai_summary=_fallback_summary(data),
        ai_insights=_fallback_insights(data),
        ai_suggestions=_fallback_suggestions(data),
        persona_description=_fallback_persona_desc(data),
        quality=ProfileReportQuality(passed=False, score=0.0, issues=[reason]),
        source="fallback",
    )'''
new_fb = '''    return ProfileReportResponse(
        ai_summary=_fallback_summary(data),
        ai_insights=_fallback_insights(data),
        ai_suggestions=_fallback_suggestions(data),
        persona_description=_fallback_persona_desc(data),
        page_analyses=_fallback_page_analyses(data),
        reading_style=_fallback_reading_style(data),
        closing=_fallback_closing(data),
        quality=ProfileReportQuality(passed=False, score=0.0, issues=[reason]),
        source="fallback",
    )'''
content = content.replace(old_fb, new_fb)

with open('d:/大三下/实训/project/test/ai-service/app/services/profile_report_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('All ai-service updates complete')
