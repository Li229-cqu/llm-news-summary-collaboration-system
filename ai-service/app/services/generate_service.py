from __future__ import annotations

from typing import List, Optional, Tuple
import re
import logging
import asyncio

from app.common.exceptions import AIServiceException
from app.core.config import settings
from app.schemas.generate import GenerateRequest, GenerateResponse, NewsElement, ConsistencyCheck
from app.schemas.evidence import EvidenceChain, EvidenceRequest, EvidenceResponse
from app.services.llm_client import call_llm, call_summary_llm
from app.services.prompt_builder import build_messages
from app.services.llm_parser import parse_llm_response
from app.services.evidence_service import evaluate_evidence, evaluate_evidence_mock

logger = logging.getLogger(__name__)

AI_SOURCE_VALUES = {"mock", "llm", "fallback", "demo", "nlp_rule", "rule", "deepseek", "zhipu", "glm", "unknown"}


def _normalize_generation_source(value: str | None, default: str = "unknown") -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return default
    if raw in {"llm_deepseek", "summary_deepseek"}:
        return "deepseek"
    if raw in {"llm_zhipu", "glm-4", "glm4"}:
        return "zhipu"
    if raw in {"local", "local_rules", "nlp", "algorithm", "extractive"}:
        return "nlp_rule"
    if raw in AI_SOURCE_VALUES:
        return raw
    return default

CLICKBAIT_WORDS = [
    "震撼", "炸裂", "万万没想到", "惊呆", "震惊", "吓尿", "跪了",
    "惨了", "绝了", "神了", "逆天", "厉害了", "毁三观", "吓傻",
    "哭晕", "吓哭", "吓瘫", "吓疯", "吓呆", "吓傻了", "吓懵",
    "看傻", "看呆", "看懵", "看跪", "看哭", "听傻", "听呆",
    "惊呆了", "震惊了", "吓尿了", "跪了跪了", "绝绝子", "YYDS",
    "OMG", "卧槽", "我靠", "我勒个去", "天呐", "我的天",
    "重磅", "炸裂了", "爆了", "刷屏", "沸腾", "疯传", "刷屏了",
    "沸腾了", "疯传了", "燃爆", "燃炸", "燃爆了", "燃炸了",
    "揭秘", "曝光", "内幕", "真相", "惊天", "惊人", "诡异",
    "离奇", "惊悚", "恐怖", "吓人", "可怕", "要命", "危险",
    "必读", "必看", "必转", "赶紧", "速看", "快看", "立刻",
    "马上", "现在", "赶紧看", "速来", "快来看", "快来围观",
    "不看后悔", "看了后悔", "不看亏大", "看了吓一跳", "看了沉默",
    "看了流泪", "看了心碎", "看了崩溃", "看了窒息", "看了抑郁",
    "深度好文", "深度解析", "深度揭秘", "深度曝光", "深度好文",
]


def _remove_clickbait(text: str) -> str:
    for word in CLICKBAIT_WORDS:
        text = text.replace(word, "")
    return text.strip()


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r'[。！？；\n]+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _extract_keywords(text: str, max_keywords: int = 5) -> list[str]:
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
    sentences = _split_sentences(input_text)
    keywords = _extract_keywords(input_text, max_keywords=3)

    if not sentences:
        return ["新闻标题"] * title_count

    titles = []
    main_topic = keywords[0] if keywords else sentences[0][:20]

    for i in range(title_count):
        if i < len(sentences):
            title = sentences[i]
        else:
            title = sentences[0]

        if len(title) > 30:
            title = title[:30] + "..."

        titles.append(title)

    while len(titles) < title_count:
        if keywords:
            title = f"{keywords[0]}相关新闻"
            if len(keywords) > 1:
                title = f"{keywords[0]}与{keywords[1]}领域新动态"
        else:
            title = f"新闻动态第{len(titles) + 1}"
        titles.append(title)

    return [_remove_clickbait(title) for title in titles[:title_count]]


def _generate_summary_short(
    input_text: str,
    summary_style: str,
    summary_type: str
) -> str:
    sentences = _split_sentences(input_text)
    text_length = len(input_text)

    if not sentences:
        return "文本过短，无法生成摘要"

    min_length = 50
    max_length = 150

    target_length = int(text_length * 0.2)
    target_length = max(min_length, min(target_length, max_length))

    if summary_type == "extract":
        short_summary = ""
        for sentence in sentences:
            if len(short_summary) + len(sentence) <= target_length:
                short_summary += sentence
            else:
                remaining = target_length - len(short_summary)
                if remaining > 10:
                    short_summary += sentence[:remaining]
                break
        if not short_summary:
            short_summary = sentences[0][:target_length]
    else:
        keywords = _extract_keywords(input_text, max_keywords=3)
        key_keywords = "、".join(keywords[:2]) if keywords else "相关内容"
        first_part = ""
        for sentence in sentences[:2]:
            if len(first_part) + len(sentence) <= target_length - 20:
                first_part += sentence
            else:
                break
        short_summary = f"{key_keywords}：{first_part}"

    short_summary = short_summary[:max_length].rstrip('，。！？；') + "。"

    if summary_style == "客观正式":
        short_summary = f"据报道，{short_summary}"
    elif summary_style == "通俗易懂":
        short_summary = f"简单来说，{short_summary}"

    return _remove_clickbait(short_summary)


def _generate_summary_long(
    input_text: str,
    summary_style: str,
    summary_type: str
) -> str:
    sentences = _split_sentences(input_text)
    text_length = len(input_text)

    if not sentences:
        return "文本过短，无法生成长摘要"

    min_length = 300
    max_length = 800

    target_length = int(text_length * 0.6)
    target_length = max(min_length, min(target_length, max_length))

    if summary_type == "extract":
        long_summary = ""
        for sentence in sentences:
            if len(long_summary) + len(sentence) <= target_length:
                long_summary += sentence
            else:
                remaining = target_length - len(long_summary)
                if remaining > 50:
                    long_summary += sentence[:remaining]
                break
        if not long_summary:
            long_summary = "".join(sentences[:min(10, len(sentences))])
    else:
        keywords = _extract_keywords(input_text, max_keywords=5)
        key_keywords = "、".join(keywords[:3]) if keywords else "相关内容"
        
        first_part = ""
        for sentence in sentences[:15]:
            if len(first_part) + len(sentence) <= target_length - 150:
                first_part += sentence
            else:
                break
        
        background_info = "这一事件的背景可以追溯到前期的相关政策铺垫，随着近年来相关领域的持续发展，此次举措具有重要的里程碑意义。"
        impact_info = "业内人士认为，这一举措将对相关行业产生深远影响，不仅能够提升整体效率，还将推动行业向更高质量方向发展。"
        
        long_summary = f"本文围绕{key_keywords}展开，详细介绍了相关领域的最新发展动态。{first_part}。{background_info}。{impact_info}。这些变化不仅反映了当前行业趋势，也为未来发展提供了重要参考，值得持续关注。"

    long_summary = long_summary[:max_length].rstrip('，。！？；') + "。"

    if summary_style == "客观正式":
        long_summary = f"综合相关信息来看，{long_summary}"
    elif summary_style == "通俗易懂":
        long_summary = f"说得更通俗一点，{long_summary}"

    return _remove_clickbait(long_summary)


def _generate_summary_points(input_text: str, summary_type: str) -> list[str]:
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


def generate_mock_response(
    request: GenerateRequest,
    *,
    source: str = "mock",
    generation_source: str = "mock",
    provider: str = "local",
    model: str = "rule-based",
    fallback_reason: str | None = None,
) -> GenerateResponse:
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

    evidence_chain = None
    evidence_chain_short = None
    evidence_chain_long = None
    risk_level = None
    risk_details = None
    evidence_coverage = None

    if not request.skip_evidence:
        if summary_short:
            evidence_request_short = EvidenceRequest(
                summary_text=summary_short,
                original_text=input_text,
                news_id=0,
                summary_type=request.summary_type
            )
            evidence_response_short = evaluate_evidence_mock(evidence_request_short)
            evidence_chain_short = evidence_response_short.evidence_chain

        if summary_long:
            evidence_request_long = EvidenceRequest(
                summary_text=summary_long,
                original_text=input_text,
                news_id=0,
                summary_type=request.summary_type
            )
            evidence_response_long = evaluate_evidence_mock(evidence_request_long)
            evidence_chain_long = evidence_response_long.evidence_chain

        combined_text = summary_short + summary_long
        if combined_text:
            evidence_request = EvidenceRequest(
                summary_text=combined_text,
                original_text=input_text,
                news_id=0,
                summary_type=request.summary_type
            )
            evidence_response = evaluate_evidence_mock(evidence_request)
            evidence_chain = evidence_response.evidence_chain
            risk_level = evidence_response.risk_level
            risk_details = evidence_response.risk_details
            evidence_coverage = evidence_response.evidence_chain.evidence_coverage if evidence_response.evidence_chain else None

    return GenerateResponse(
        candidate_titles=candidate_titles,
        summary_short=summary_short,
        summary_long=summary_long,
        summary_points=summary_points,
        keywords=keywords,
        elements=elements,
        consistency=consistency,
        source=_normalize_generation_source(source, "mock"),
        generation_source=_normalize_generation_source(generation_source, _normalize_generation_source(source, "mock")),
        provider=provider,
        model=model,
        fallback_reason=fallback_reason,
        evidence_chain=evidence_chain,
        evidence_chain_short=evidence_chain_short,
        evidence_chain_long=evidence_chain_long,
        risk_level=risk_level,
        risk_details=risk_details,
        evidence_coverage=evidence_coverage
    )


async def _evaluate_evidence_background(
    summary_text: str,
    original_text: str,
    news_id: int = 0,
    summary_type: str = "generate"
) -> Optional[EvidenceResponse]:
    try:
        evidence_request = EvidenceRequest(
            summary_text=summary_text,
            original_text=original_text,
            news_id=news_id,
            summary_type=summary_type
        )
        return await evaluate_evidence(evidence_request)
    except Exception as e:
        logger.error(f"后台证据评估任务失败: {type(e).__name__}: {str(e)}")
        return None


async def generate_title_summary(request: GenerateRequest) -> GenerateResponse:
    if not request.input_text.strip():
        raise AIServiceException(code=400, message="输入文本不能为空")

    if not 1 <= request.title_count <= 5:
        raise AIServiceException(code=400, message="标题数量必须在 1-5 范围内")

    if not settings.summary_llm_enabled:
        logger.info("LLM 未启用，使用动态 mock 生成响应")
        return generate_mock_response(
            request,
            source="nlp_rule",
            generation_source="nlp_rule",
            provider="local",
            model="rule-based",
        )

    if settings.summary_llm_enabled:
        logger.info(f"双AI架构已启用，准备调用 DeepSeek 生成摘要: model={settings.summary_llm_model}")

        try:
            short_response = None
            long_response = None

            if request.summary_length in ("short", "both"):
                logger.info("开始生成短摘要（独立调用）")
                short_messages = build_messages(request, "short")
                short_llm_response = await call_summary_llm(short_messages)
                
                logger.info(f"短摘要原始响应长度: {len(short_llm_response)}")
                
                short_response = parse_llm_response(
                    short_llm_response,
                    title_count=request.title_count,
                    summary_length="short"
                )

            if request.summary_length in ("long", "both"):
                logger.info("开始生成长摘要（独立调用）")
                long_messages = build_messages(request, "long")
                long_llm_response = await call_summary_llm(long_messages)
                
                logger.info(f"长摘要原始响应长度: {len(long_llm_response)}")
                
                long_response = parse_llm_response(
                    long_llm_response,
                    title_count=request.title_count,
                    summary_length="long"
                )

            if short_response is None and long_response is None:
                logger.warning("长短摘要都无法解析，fallback 到 mock")
                return generate_mock_response(
                    request,
                    source="fallback",
                    generation_source="fallback",
                    provider=settings.summary_llm_provider,
                    model=settings.summary_llm_model,
                    fallback_reason="LLM response parse failed",
                )

            response = short_response if short_response else long_response
            response.source = "llm"
            response.generation_source = _normalize_generation_source(settings.summary_llm_provider, "llm")
            response.provider = settings.summary_llm_provider
            response.model = settings.summary_llm_model
            response.fallback_reason = None
            
            if short_response and long_response:
                response.summary_short = short_response.summary_short
                response.summary_long = long_response.summary_long
                response.summary_points = short_response.summary_points
                response.keywords = short_response.keywords
                response.elements = short_response.elements
                response.consistency = short_response.consistency

            if response is not None:
                logger.info("DeepSeek 调用成功，返回有效响应")
                logger.info(f"解析后 - 短摘要长度: {len(response.summary_short)}, 长摘要长度: {len(response.summary_long)}")
                logger.info(f"短摘要前100字: {response.summary_short[:100]}")
                logger.info(f"长摘要前100字: {response.summary_long[:100]}")

                if not request.skip_evidence:
                    logger.info("正在并行执行证据评估")
                    evidence_tasks = []

                    if response.summary_short:
                        evidence_tasks.append(_evaluate_evidence_background(
                            response.summary_short,
                            request.input_text,
                            0,
                            request.summary_type
                        ))

                    if response.summary_long:
                        evidence_tasks.append(_evaluate_evidence_background(
                            response.summary_long,
                            request.input_text,
                            0,
                            request.summary_type
                        ))

                    if evidence_tasks:
                        results = await asyncio.gather(*evidence_tasks, return_exceptions=True)

                        if response.summary_short and results[0] and not isinstance(results[0], Exception):
                            response.evidence_chain_short = results[0].evidence_chain
                            response.evidence_chain = results[0].evidence_chain
                            response.risk_level = results[0].risk_level
                            response.risk_details = results[0].risk_details
                            response.evidence_coverage = results[0].evidence_chain.evidence_coverage if results[0].evidence_chain else None

                        if response.summary_long and len(results) > 1 and results[1] and not isinstance(results[1], Exception):
                            response.evidence_chain_long = results[1].evidence_chain

                return response

            logger.warning("DeepSeek 返回内容无法解析，fallback 到 mock")
            return generate_mock_response(
                request,
                source="fallback",
                generation_source="fallback",
                provider=settings.summary_llm_provider,
                model=settings.summary_llm_model,
                fallback_reason="LLM response parse failed",
            )

        except ValueError as e:
            logger.warning(f"DeepSeek 参数错误，fallback 到 mock: {str(e)}")
            return generate_mock_response(
                request,
                source="fallback",
                generation_source="fallback",
                provider=settings.summary_llm_provider,
                model=settings.summary_llm_model,
                fallback_reason=str(e),
            )

        except Exception as e:
            logger.warning(f"DeepSeek 调用失败，fallback 到 mock: {type(e).__name__}: {str(e)}")
            return generate_mock_response(
                request,
                source="fallback",
                generation_source="fallback",
                provider=settings.summary_llm_provider,
                model=settings.summary_llm_model,
                fallback_reason=f"{type(e).__name__}: {str(e)}",
            )

    else:
        logger.info(f"单AI模式已启用，准备调用智谱 GLM: model={settings.summary_llm_model}")

        try:
            messages = build_messages(request)
            llm_response = await call_llm(messages)

            response = parse_llm_response(
                llm_response,
                title_count=request.title_count,
                summary_length=request.summary_length
            )
            response.source = "llm"
            response.generation_source = _normalize_generation_source(settings.summary_llm_provider, "llm")
            response.provider = settings.summary_llm_provider
            response.model = settings.summary_llm_model
            response.fallback_reason = None

            if response is not None:
                logger.info("智谱 GLM 调用成功，返回有效响应")

                if not request.skip_evidence:
                    logger.info("正在并行执行证据评估")
                    evidence_tasks = []

                    if response.summary_short:
                        evidence_tasks.append(_evaluate_evidence_background(
                            response.summary_short,
                            request.input_text,
                            0,
                            request.summary_type
                        ))

                    if response.summary_long:
                        evidence_tasks.append(_evaluate_evidence_background(
                            response.summary_long,
                            request.input_text,
                            0,
                            request.summary_type
                        ))

                    if evidence_tasks:
                        results = await asyncio.gather(*evidence_tasks, return_exceptions=True)

                        if response.summary_short and results[0] and not isinstance(results[0], Exception):
                            response.evidence_chain_short = results[0].evidence_chain
                            response.evidence_chain = results[0].evidence_chain
                            response.risk_level = results[0].risk_level
                            response.risk_details = results[0].risk_details
                            response.evidence_coverage = results[0].evidence_chain.evidence_coverage if results[0].evidence_chain else None

                        if response.summary_long and len(results) > 1 and results[1] and not isinstance(results[1], Exception):
                            response.evidence_chain_long = results[1].evidence_chain

                return response

            logger.warning("智谱 GLM 返回内容无法解析，fallback 到 mock")
            return generate_mock_response(
                request,
                source="fallback",
                generation_source="fallback",
                provider=settings.summary_llm_provider,
                model=settings.summary_llm_model,
                fallback_reason="LLM response parse failed",
            )

        except ValueError as e:
            logger.warning(f"智谱 LLM 参数错误，fallback 到 mock: {str(e)}")
            return generate_mock_response(
                request,
                source="fallback",
                generation_source="fallback",
                provider=settings.summary_llm_provider,
                model=settings.summary_llm_model,
                fallback_reason=str(e),
            )

        except Exception as e:
            logger.warning(f"智谱 LLM 调用失败，fallback 到 mock: {type(e).__name__}: {str(e)}")
            return generate_mock_response(
                request,
                source="fallback",
                generation_source="fallback",
                provider=settings.summary_llm_provider,
                model=settings.summary_llm_model,
                fallback_reason=f"{type(e).__name__}: {str(e)}",
            )
