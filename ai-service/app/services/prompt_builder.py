""""""

from __future__ import annotations

from typing import List


from app.schemas.generate import GenerateRequest


def build_generate_prompt(request: GenerateRequest) -> str:
    """
    构造标题摘要生成 prompt。

    要求：
    - 模型必须只返回 JSON，不要 markdown，不要解释文字
    - JSON 字段必须完整，符合 GenerateResponse 结构
    """

    summary_type_desc = "抽取原文关键句" if request.summary_type == "extract" else "重新概括组织"
    summary_length_desc = {
        "short": "仅返回短摘要",
        "long": "仅返回长摘要",
        "both": "同时返回短摘要和长摘要",
    }.get(request.summary_length, "同时返回短摘要和长摘要")

    prompt = f"""你是一个专业的新闻编辑 AI。根据以下要求生成新闻标题、摘要和分析结果。

【输入新闻】
{request.input_text}

【生成要求】
1. 标题数量：{request.title_count} 个
   - 风格：{request.title_style}
   - 生成高质量、不同角度的标题

2. 摘要类型：{summary_type_desc}
   - 风格：{request.summary_style}
   - 长度配置：{summary_length_desc}

3. 关键词提取：自动识别 3-8 个关键词
4. 新闻要素识别：识别 who、what、when、where、why、how
5. 一致性评估：评分 0-100，风险等级 low/medium/high

【返回格式】
只返回一个 JSON 对象，不要 markdown 包裹，不要代码块，不要任何解释文字。

JSON 结构：
{{
  "candidate_titles": ["标题1", "标题2", ...],
  "summary_short": "短摘要文本（{request.summary_length}为short或both时必须有内容）",
  "summary_long": "长摘要文本（{request.summary_length}为long或both时必须有内容）",
  "summary_points": ["要点1", "要点2", "要点3"],
  "keywords": ["关键词1", "关键词2", ...],
  "elements": {{
    "who": "新闻主体",
    "what": "新闻事件",
    "when": "新闻时间",
    "where": "新闻地点",
    "why": "新闻原因",
    "how": "新闻方式"
  }},
  "consistency": {{
    "score": 85,
    "risk_level": "low",
    "issues": ["潜在问题1"],
    "suggestions": ["改进建议1"]
  }}
}}

【字段规则】
- candidate_titles 的数量必须恰好等于 {request.title_count}
- risk_level 只能是 low、medium、high 之一
- score 必须是 0-100 之间的整数
- keywords 数量建议 3-8 个
- elements 的所有字段都必须有实际内容
- summary_short/summary_long 必须根据 summary_length 配置决定是否为空
- 标题和摘要必须忠于原文，不要编造原文没有的信息

【开始生成】
请直接返回 JSON，不要其他内容。
"""
    return prompt


def build_messages(request: GenerateRequest) -> list[dict]:
    """
    构造消息列表供 LLM 调用。

    返回格式：
    [{"role": "user", "content": "...prompt..."}]
    """
    prompt = build_generate_prompt(request)
    return [{"role": "user", "content": prompt}]
