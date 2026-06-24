"""
LLM 返回结果解析和修复模块。

负责：
1. 清理 LLM 返回的 markdown 包裹
2. 解析 JSON
3. 修复字段缺失或类型错误
4. 映射中文风险等级为英文
5. 确保能构造出有效的 GenerateResponse
"""

import json
import re
import logging
from typing import Any

from app.schemas.generate import GenerateResponse, NewsElement, ConsistencyCheck

logger = logging.getLogger(__name__)


def clean_markdown_json(content: str) -> str:
    """
    清理 LLM 返回的 markdown 包裹。

    处理以下格式：
    - ```json ... ```
    - ``` ... ```
    - json ... 等

    返回干净的 JSON 字符串。
    """
    content = content.strip()

    # 移除 ```json 和 ``` 包裹
    if content.startswith("```json"):
        content = content[7:]  # 移除 ```json
    elif content.startswith("```"):
        content = content[3:]  # 移除 ```

    if content.endswith("```"):
        content = content[:-3]  # 移除末尾 ```

    content = content.strip()

    return content


def parse_json_safe(content: str) -> dict | None:
    """
    安全地解析 JSON 字符串。

    如果解析失败，记录错误并返回 None。
    """
    try:
        content = clean_markdown_json(content)
        data = json.loads(content)
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"JSON 解析失败: {str(e)}")
        return None
    except Exception as e:
        logger.warning(f"JSON 解析异常: {type(e).__name__}: {str(e)}")
        return None


def map_risk_level(value: Any) -> str:
    """
    将风险等级值映射为标准的英文形式。

    支持：
    - low / 低风险
    - medium / 中风险
    - high / 高风险
    """
    if isinstance(value, str):
        value = value.lower().strip()

        # 直接匹配英文
        if value in ("low", "medium", "high"):
            return value

        # 映射中文
        if "低" in value:
            return "low"
        if "中" in value or "中等" in value:
            return "medium"
        if "高" in value:
            return "high"

    # 默认返回 low
    return "low"


def ensure_integer(value: Any, default: int = 80) -> int:
    """
    确保值是整数。

    如果无法转换则返回默认值。
    """
    try:
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            return int(value.strip())
    except (ValueError, TypeError):
        pass

    logger.warning(f"无法将 {value} 转换为整数，使用默认值 {default}")
    return default


def repair_consistency_check(data: dict) -> ConsistencyCheck:
    """
    修复并验证 ConsistencyCheck 数据。

    确保：
    - score: 0-100 整数
    - risk_level: low/medium/high
    - issues: 列表（缺失则为空列表）
    - suggestions: 列表（缺失则为空列表）
    """
    consistency = data.get("consistency", {})

    # 修复 score
    score = ensure_integer(consistency.get("score"), default=80)
    score = max(0, min(100, score))  # 限制在 0-100

    # 修复 risk_level
    risk_level = map_risk_level(consistency.get("risk_level", "low"))

    # 修复 issues（列表）
    issues = consistency.get("issues", [])
    if not isinstance(issues, list):
        issues = [str(issues)] if issues else []

    # 修复 suggestions（列表）
    suggestions = consistency.get("suggestions", [])
    if not isinstance(suggestions, list):
        suggestions = [str(suggestions)] if suggestions else []

    return ConsistencyCheck(
        score=score,
        risk_level=risk_level,
        issues=issues if issues else ["无明显问题"],
        suggestions=suggestions if suggestions else ["文本质量满足条件"],
    )


def repair_news_element(data: dict) -> NewsElement:
    """
    修复并验证 NewsElement 数据。

    确保所有字段都有值，缺失则使用默认值。
    """
    elements = data.get("elements", {})

    # 定义默认值
    defaults = {
        "who": "相关主体",
        "what": "相关事件",
        "when": "近期",
        "where": "相关地区",
        "why": "事件原因需进一步分析",
        "how": "通过相关措施或行动",
    }

    # 修复每个字段
    fixed = {}
    for key in ["who", "what", "when", "where", "why", "how"]:
        value = elements.get(key, "")
        if isinstance(value, str) and value.strip():
            fixed[key] = value[:100]  # 限制长度
        else:
            fixed[key] = defaults[key]

    return NewsElement(**fixed)


def repair_candidate_titles(data: dict, title_count: int) -> list[str]:
    """
    修复 candidate_titles 列表。

    规则：
    - 如果数量不足，使用默认标题补足
    - 如果数量过多，截断到 title_count
    """
    titles = data.get("candidate_titles", [])

    if not isinstance(titles, list):
        titles = []

    # 转换非字符串元素
    titles = [str(t) for t in titles if t]

    # 补足不足的标题
    while len(titles) < title_count:
        titles.append(f"新闻标题 {len(titles) + 1}")

    # 截断过多的标题
    titles = titles[:title_count]

    return titles


def repair_keywords(data: dict) -> list[str]:
    """
    修复 keywords 列表。

    规则：
    - 转换为字符串列表
    - 移除空字符串
    - 保留 3-8 个
    """
    keywords = data.get("keywords", [])

    if not isinstance(keywords, list):
        keywords = []

    # 转换非字符串元素并过滤空值
    keywords = [str(k).strip() for k in keywords if k]
    keywords = [k for k in keywords if k]  # 再次过滤空字符串

    # 保留 3-8 个
    if len(keywords) < 3:
        # 补足默认关键词
        while len(keywords) < 3:
            keywords.append(f"关键词{len(keywords) + 1}")
    else:
        keywords = keywords[:8]

    return keywords


def repair_summaries(data: dict, summary_length: str) -> tuple[str, str]:
    """
    修复 summary_short 和 summary_long。

    规则：
    - summary_length=short：summary_short 有内容，summary_long 为空
    - summary_length=long：summary_long 有内容，summary_short 为空
    - summary_length=both：两者都有内容
    """
    summary_short = data.get("summary_short", "").strip() if data.get("summary_short") else ""
    summary_long = data.get("summary_long", "").strip() if data.get("summary_long") else ""

    if summary_length == "short":
        if not summary_short:
            summary_short = "摘要内容"
        summary_long = ""
    elif summary_length == "long":
        if not summary_long:
            summary_long = "摘要内容"
        summary_short = ""
    elif summary_length == "both":
        if not summary_short:
            summary_short = "短摘要内容"
        if not summary_long:
            summary_long = "长摘要内容"

    return summary_short, summary_long


def repair_summary_points(data: dict) -> list[str]:
    """
    修复 summary_points 列表。

    规则：
    - 转换为字符串列表
    - 移除空字符串
    - 至少保留 1 个，最多 5 个
    """
    points = data.get("summary_points", [])

    if not isinstance(points, list):
        points = []

    # 转换非字符串元素并过滤空值
    points = [str(p).strip() for p in points if p]
    points = [p for p in points if p]  # 再次过滤空字符串

    # 确保有内容
    if not points:
        points = ["主要内容已记录"]

    # 限制数量
    points = points[:5]

    return points


def parse_llm_response(content: str, title_count: int, summary_length: str) -> GenerateResponse | None:
    """
    解析 LLM 返回的内容，构造 GenerateResponse。

    流程：
    1. 清理 markdown
    2. 解析 JSON
    3. 修复缺失和类型错误的字段
    4. 构造 GenerateResponse

    如果无法构造有效的响应，返回 None。
    """
    # 解析 JSON
    data = parse_json_safe(content)
    if data is None:
        logger.error("无法解析 LLM 返回的 JSON")
        return None

    try:
        # 修复各字段
        candidate_titles = repair_candidate_titles(data, title_count)
        summary_short, summary_long = repair_summaries(data, summary_length)
        summary_points = repair_summary_points(data)
        keywords = repair_keywords(data)
        elements = repair_news_element(data)
        consistency = repair_consistency_check(data)

        # 构造 GenerateResponse
        response = GenerateResponse(
            candidate_titles=candidate_titles,
            summary_short=summary_short,
            summary_long=summary_long,
            summary_points=summary_points,
            keywords=keywords,
            elements=elements,
            consistency=consistency,
            source="llm",
        )

        logger.info("LLM 返回成功解析并修复")
        return response

    except Exception as e:
        logger.error(f"构造 GenerateResponse 失败: {type(e).__name__}: {str(e)}")
        return None
