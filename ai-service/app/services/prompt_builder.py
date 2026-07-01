""""""

from __future__ import annotations

from typing import List


from app.schemas.generate import GenerateRequest


def build_generate_prompt(request: GenerateRequest, summary_mode: str = "both") -> str:
    """
    构造标题摘要生成 prompt。

    参数：
    - summary_mode: "short" | "long" | "both" - 指定生成哪种摘要

    要求：
    - 模型必须只返回 JSON，不要 markdown，不要解释文字
    - JSON 字段必须完整，符合 GenerateResponse 结构
    """

    summary_type_desc = "抽取原文关键句" if request.summary_type == "extract" else "重新概括组织"

    if summary_mode == "short":
        summary_prompt = """2. 摘要生成：
   - 仅生成短摘要（summary_short）
   - 长度：50-150 字
   - 要求：高度浓缩核心信息，只保留最重要的事实和数据
   - 不要包含任何背景信息或分析"""
        return_field = '"summary_short": "短摘要文本（50-150字）"'
    elif summary_mode == "long":
        summary_prompt = """2. 摘要生成：
   - 仅生成长摘要（summary_long）
   - 长度：300-600 字
   - 要求：详细展开关键内容，包含背景信息、具体数据、分析解读
   - 必须包含短摘要中没有的额外细节和深度信息"""
        return_field = '"summary_long": "长摘要文本（300-600字）"'
    else:
        summary_prompt = """2. 摘要生成：
   - 短摘要（summary_short）：50-150 字，高度浓缩核心信息
   - 长摘要（summary_long）：300-600 字，详细展开关键内容
   - 长短摘要必须有明显区别，长摘要应包含短摘要没有的背景、细节和分析"""
        return_field = '"summary_short": "短摘要文本（50-150字）",\n  "summary_long": "长摘要文本（300-600字）"'

    prompt = f"""你是一个专业的新闻编辑 AI。根据以下要求生成新闻标题、摘要和分析结果。

【输入新闻】
{request.input_text}

【生成要求】
1. 标题数量：{request.title_count} 个
   - 风格：{request.title_style}
   - 生成高质量、不同角度的标题

{summary_prompt}

3. 关键词提取：自动识别 3-8 个关键词
4. 新闻要素识别：识别 who、what、when、where、why、how
5. 一致性评估：评分 0-100，风险等级 low/medium/high

【返回格式】
只返回一个 JSON 对象，不要 markdown 包裹，不要代码块，不要任何解释文字。

JSON 结构：
{{
  "candidate_titles": ["标题1", "标题2", ...],
  {return_field},
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
- 标题和摘要必须忠于原文，不要编造原文没有的信息

【开始生成】
请直接返回 JSON，不要其他内容。
"""
    return prompt


def build_messages(request: GenerateRequest, summary_mode: str = "both") -> list[dict]:
    """
    构造消息列表供 LLM 调用。

    参数：
    - summary_mode: "short" | "long" | "both" - 指定生成哪种摘要

    返回格式：
    [{"role": "user", "content": "...prompt..."}]
    """
    prompt = build_generate_prompt(request, summary_mode)
    return [{"role": "user", "content": prompt}]
