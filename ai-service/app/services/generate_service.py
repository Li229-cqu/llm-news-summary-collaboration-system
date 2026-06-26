from __future__ import annotations

from typing import List
import re
import logging

from app.common.exceptions import AIServiceException
from app.core.config import settings
from app.schemas.generate import GenerateRequest, GenerateResponse, NewsElement, ConsistencyCheck
from app.services.llm_client import call_llm
from app.services.prompt_builder import build_messages
from app.services.llm_parser import parse_llm_response

logger = logging.getLogger(__name__)


def _split_sentences(text: str) -> list[str]:
    """按中文句号、问号、感叹号、分号等分割句子。"""
    sentences = re.split(r'[。！？；\n]+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _extract_keywords(text: str, max_keywords: int = 5) -> list[str]:
    """从文本中提取关键词（简单实现：提取较长的词汇）。"""
    words = re.findall(r'[一-鿿]{2,}', text)
    keyword_freq = {}
    for word in words:
        keyword_freq[word] = keyword_freq.get(word, 0) + 1

    sorted_keywords = sorted(keyword_freq.items(), key=lambda x: (-x[1], -len(x[0])))
    return [word for word, _ in sorted_keywords[:max_keywords]]


def _generate_dynamic_titles(
    input_text: str,
    title_count: int,
    title_style: str
) -> list[str]:
    """根据输入文本动态生成标题（去除标题党模板）。"""
    sentences = _split_sentences(input_text)
    keywords = _extract_keywords(input_text, max_keywords=3)

    if not sentences:
        return ["新闻标题"] * title_count

    titles = []
    main_topic = keywords[0] if keywords else sentences[0][:20]

    # 从输入文本中提取合适的标题
    for i in range(title_count):
        if i < len(sentences):
            title = sentences[i]
        else:
            title = sentences[0]

        # 超过 30 字则裁剪
        if len(title) > 30:
            title = title[:30] + "..."

        titles.append(title)

    # 如果需要更多标题，使用不同组合
    while len(titles) < title_count:
        if keywords:
            title = f"{keywords[0]}相关新闻"
            if len(keywords) > 1:
                title = f"{keywords[0]}与{keywords[1]}领域新动态"
        else:
            title = f"新闻动态第{len(titles) + 1}"
        titles.append(title)

    return titles[:title_count]


def _generate_summary_short(
    input_text: str,
    summary_style: str,
    summary_type: str
) -> str:
    """生成短摘要（改为从输入文本提取前两句）。"""
    sentences = _split_sentences(input_text)

    if not sentences:
        return "文本过短，无法生成摘要"

    # 直接提取前两句作为摘要
    short_summary = ""
    if len(sentences) >= 2:
        short_summary = sentences[0] + sentences[1]
    elif len(sentences) == 1:
        short_summary = sentences[0]
    else:
        return "文本过短，无法生成摘要"

    # 根据风格进行简单调整
    if summary_style == "简明扼要":
        if len(short_summary) > 80:
            short_summary = short_summary[:80] + "..."
    elif summary_style == "客观正式":
        short_summary = f"根据相关报道，{short_summary}"
    elif summary_style == "通俗易懂":
        short_summary = f"简单来说，{short_summary}"

    return short_summary


def _generate_summary_long(
    input_text: str,
    summary_style: str,
    summary_type: str
) -> str:
    """生成长摘要。"""
    sentences = _split_sentences(input_text)

    if not sentences:
        return "文本过短，无法生成长摘要"

    if summary_type == "extract":
        long_summary = "".join(sentences[:min(4, len(sentences))])
    else:
        keywords = _extract_keywords(input_text, max_keywords=4)
        key_keywords = "、".join(keywords[:3]) if keywords else "相关内容"
        first_part = "".join(sentences[:min(3, len(sentences))])
        long_summary = f"本文详细介绍了{key_keywords}的最新发展。{first_part}这些进展在多个方面具有重要意义，有望在后续相关领域产生深远影响。"

    if summary_style == "简明扼要":
        if len(long_summary) > 150:
            long_summary = long_summary[:150] + "..."
    elif summary_style == "客观正式":
        long_summary = f"综合相关信息来看，{long_summary}"
    elif summary_style == "通俗易懂":
        long_summary = f"说得更通俗一点，{long_summary}"

    return long_summary


def _generate_summary_points(input_text: str, summary_type: str) -> list[str]:
    """生成摘要要点。"""
    sentences = _split_sentences(input_text)

    if not sentences:
        return []

    points = []

    if summary_type == "extract":
        for sentence in sentences[:3]:
            if len(sentence) > 5:
                points.append(sentence)
    else:
        keywords = _extract_keywords(input_text, max_keywords=5)
        for i, keyword in enumerate(keywords[:3]):
            if i < len(sentences):
                point = f"相关内容涉及{keyword}方面的重要突破"
                points.append(point)
            else:
                points.append(f"{keyword}是本文重点关注的对象")

    return points[:3] if points else ["文本内容已记录"]


def _extract_news_elements(input_text: str) -> NewsElement:
    """从文本中提取新闻六要素。"""
    sentences = _split_sentences(input_text)

    who = ""
    what = ""
    when = ""
    where = ""
    why = ""
    how = ""

    if sentences:
        first_sentence = sentences[0]

        org_patterns = ["公司", "团队", "机构", "学校", "球队", "组织", "部队", "集团"]
        for pattern in org_patterns:
            if pattern in first_sentence:
                idx = first_sentence.index(pattern)
                who = first_sentence[:idx + len(pattern)]
                break

        if not who:
            words = re.findall(r'[一-鿿]{2,}', first_sentence)
            if words:
                who = words[0]

        what = first_sentence

        time_patterns = ["2025", "2026", "今年", "去年", "日前", "近日", "昨日", "今日"]
        for pattern in time_patterns:
            if pattern in input_text:
                time_idx = input_text.index(pattern)
                time_end = min(time_idx + 20, len(input_text))
                when_candidate = input_text[time_idx:time_end].split("。")[0]
                when = when_candidate
                break

        place_patterns = ["北京", "上海", "深圳", "中国", "国", "地", "区", "市", "州"]
        for pattern in place_patterns:
            if pattern in input_text:
                idx = input_text.index(pattern)
                where = input_text[max(0, idx-2):idx+len(pattern)]
                break

        keywords = _extract_keywords(input_text, max_keywords=1)
        if keywords and len(sentences) > 1:
            why = f"为了推进{keywords[0]}的发展"

        if len(sentences) > 2:
            how = sentences[2][:30] if len(sentences[2]) > 30 else sentences[2]

    who = who or "相关主体"
    what = what or "相关事件"
    when = when or "近期"
    where = where or "相关地区"
    why = why or "事件原因仍需结合上下文进一步判断"
    how = how or "通过相关措施或行动推进"

    return NewsElement(
        who=who[:50],
        what=what[:100],
        when=when[:30],
        where=where[:30],
        why=why[:50],
        how=how[:50]
    )


def _check_consistency(input_text: str) -> ConsistencyCheck:
    """检查文本一致性和质量。"""
    score = 90
    risk_level = "low"
    issues = []
    suggestions = []

    text_length = len(input_text)
    if text_length < 50:
        score -= 20
        risk_level = "medium"
        issues.append("输入正文较短，摘要依据有限")
        suggestions.append("建议输入更多的新闻正文内容")
    elif text_length < 100:
        score -= 10
        issues.append("输入正文长度偏短")
        suggestions.append("可补充更多内容以提高摘要准确性")

    conflict_patterns = [
        ("上涨", "下跌"),
        ("增加", "减少"),
        ("上升", "下降"),
        ("利好", "利空"),
        ("成功", "失败"),
    ]

    for pattern1, pattern2 in conflict_patterns:
        if pattern1 in input_text and pattern2 in input_text:
            risk_level = "medium"
            if score > 70:
                score = 70
            issues.append(f"文本中同时出现'{pattern1}'和'{pattern2}'，可能存在表述冲突")
            suggestions.append("请检查原文是否表述清晰，避免歧义")

    if not any(keyword in input_text for keyword in ["。", "！", "？"]):
        issues.append("文本缺乏标准句式")
        suggestions.append("建议使用完整的句式结构")

    score = max(0, min(100, score))

    return ConsistencyCheck(
        score=score,
        risk_level=risk_level,
        issues=issues if issues else ["文本结构良好"],
        suggestions=suggestions if suggestions else ["文本质量满足生成条件"]
    )


def generate_mock_response(request: GenerateRequest) -> GenerateResponse:
    """
    生成动态 mock 响应。

    保留所有原有的 mock 生成逻辑，作为 fallback 或 LLM_ENABLED=false 时的默认实现。
    """
    input_text = request.input_text.strip()

    candidate_titles = _generate_dynamic_titles(
        input_text,
        request.title_count,
        request.title_style
    )

    summary_short = ""
    summary_long = ""

    if request.summary_length in ("short", "both"):
        summary_short = _generate_summary_short(
            input_text,
            request.summary_style,
            request.summary_type
        )

    if request.summary_length in ("long", "both"):
        summary_long = _generate_summary_long(
            input_text,
            request.summary_style,
            request.summary_type
        )

    summary_points = _generate_summary_points(input_text, request.summary_type)

    keywords = _extract_keywords(input_text, max_keywords=5)

    elements = _extract_news_elements(input_text)

    consistency = _check_consistency(input_text)

    return GenerateResponse(
        candidate_titles=candidate_titles,
        summary_short=summary_short,
        summary_long=summary_long,
        summary_points=summary_points,
        keywords=keywords,
        elements=elements,
        consistency=consistency,
        source="mock"
    )


def generate_title_summary(request: GenerateRequest) -> GenerateResponse:
    """
    生成标题和摘要的主函数。

    流程：
    1. 输入验证
    2. 如果 LLM_ENABLED=false，直接使用 mock
    3. 如果 LLM_ENABLED=true：
       - 构造 prompt
       - 调用智谱 GLM
       - 解析返回结果
       - 失败则 fallback 到 mock
    4. 返回 GenerateResponse
    """
    # 输入验证
    if not request.input_text.strip():
        raise AIServiceException(code=400, message="输入文本不能为空")

    if not 1 <= request.title_count <= 5:
        raise AIServiceException(code=400, message="标题数量必须在 1-5 范围内")

    # 如果 LLM 未启用，直接使用 mock
    if not settings.llm_enabled:
        logger.info("LLM 未启用，使用动态 mock 生成响应")
        return generate_mock_response(request)

    # LLM 启用，尝试调用模型
    logger.info(f"LLM 已启用，准备调用智谱 GLM: model={settings.llm_model}")

    try:
        # 构造消息
        messages = build_messages(request)

        # 调用 LLM
        llm_response = call_llm(messages)

        # 解析返回结果
        response = parse_llm_response(
            llm_response,
            title_count=request.title_count,
            summary_length=request.summary_length
        )

        if response is not None:
            logger.info("智谱 GLM 调用成功，返回有效响应")
            return response

        # 解析失败，fallback
        logger.warning("智谱 GLM 返回内容无法解析，fallback 到 mock")
        return generate_mock_response(request)

    except ValueError as e:
        # 配置错误、API Key 未配置等
        logger.warning(f"智谱 LLM 参数错误，fallback 到 mock: {str(e)}")
        return generate_mock_response(request)

    except Exception as e:
        # 网络错误、API 错误、超时等
        logger.warning(f"智谱 LLM 调用失败，fallback 到 mock: {type(e).__name__}: {str(e)}")
        return generate_mock_response(request)
