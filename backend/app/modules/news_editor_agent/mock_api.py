"""News Editor Agent — Mock API 工具模块（Phase 2 升级）。

Phase 2 升级：
- 从"静态 JSON 数据提供者"升级为"mock 任务启动入口"
- run_mock_task() → 创建 task + 启动 MockTaskRunner 后台状态机
- handle_mock_get_task() → 返回实时 task 状态（从 DB/Mock 存储读取）

用途：
- 前端 polling GET /task/{id} 获取实时进度
- 后端 MockTaskRunner 是唯一状态源（非客户端模拟）

安全规则：
- 不修改 pipeline.py
- 不修改 service.py（复用 AgentService 内部方法读取）
- 不修改 main.py
- 不修改数据库 schema
"""

from __future__ import annotations

import time
import random
import re
from typing import Any, Dict, List, Optional

# ═════════════════════════════════════════════════════════════
# 8 步元数据（与 pipeline.py STEP_META 保持一致）
# ═════════════════════════════════════════════════════════════

STEP_META_MOCK: List[Dict[str, Any]] = [
    {"name": "clean",              "label": "正文清洗",     "order": 1},
    {"name": "extract_keywords",   "label": "关键词提取",   "order": 2},
    {"name": "extract_elements",   "label": "六要素识别",   "order": 3},
    {"name": "generate_title_summary", "label": "标题摘要生成", "order": 4},
    {"name": "match_topic",        "label": "话题匹配",     "order": 5},
    {"name": "judge_timeline",     "label": "时间线适配",   "order": 6},
    {"name": "check_consistency",  "label": "一致性检查",   "order": 7},
    {"name": "edit_suggestions",   "label": "编辑建议生成", "order": 8},
]


def _normalize_mock_text(text: str, limit: int) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return ""
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip("，。！？；;,:： ") + "..."


def _build_mock_generate_output(
    input_text: str,
    pipeline_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base = dict(MOCK_STEP_OUTPUTS["generate_title_summary"])
    params = pipeline_params or {}

    title_count = params.get("title_count", len(base.get("candidate_titles", [])) or 3)
    try:
        title_count = max(1, min(5, int(title_count)))
    except Exception:
        title_count = 3

    summary_type = str(params.get("summary_type", "generate"))
    summary_style = str(params.get("summary_style", "简明扼要"))
    title_style = str(params.get("title_style", "客观新闻型"))
    summary_length = str(params.get("summary_length", "both"))

    sentences = [s.strip() for s in re.split(r"[。！？；\n]+", input_text or "") if s.strip()]
    seed_text = sentences[0] if sentences else (input_text or base["summary_short"] or "新闻内容")

    def build_title(seed: str, index: int) -> str:
        title = _normalize_mock_text(seed, 26) or f"新闻标题{index + 1}"
        if title_style == "吸引点击型":
            return f"重磅：{title}"
        if title_style == "简洁概括型":
            return _normalize_mock_text(title, 18) or f"标题{index + 1}"
        return title

    titles = [build_title(sentences[i] if i < len(sentences) else seed_text, i) for i in range(title_count)]
    while len(titles) < title_count:
        titles.append(build_title(seed_text, len(titles)))

    if summary_type == "extract":
        short_summary = _normalize_mock_text(input_text or base["summary_short"], 120)
        long_summary = _normalize_mock_text(input_text or base["summary_long"], 360)
    else:
        short_summary = _normalize_mock_text(f"综合来看，{input_text or base['summary_short']}", 140)
        long_summary = _normalize_mock_text(f"进一步整理后可见，{input_text or base['summary_long']}", 420)

    if summary_style == "客观正式":
        short_summary = f"据报道，{short_summary}" if short_summary else short_summary
        long_summary = f"综合来看，{long_summary}" if long_summary else long_summary
    elif summary_style == "通俗易懂":
        short_summary = f"简单来说，{short_summary}" if short_summary else short_summary
        long_summary = f"换句话说，{long_summary}" if long_summary else long_summary

    if summary_length == "short":
        long_summary = ""
    elif summary_length == "long":
        short_summary = ""

    summary_points = list(base.get("summary_points", []))
    if summary_type == "extract" and sentences:
        summary_points = sentences[:3]
    elif input_text:
        summary_points = [p for p in (
            _normalize_mock_text(seed, 28)
            for seed in sentences[:3]
        ) if p]

    return {
        **base,
        "candidate_titles": titles[:title_count],
        "summary_short": short_summary,
        "summary_long": long_summary,
        "summary_points": summary_points[:5],
        "summary_length": summary_length,
        "title_count": title_count,
        "summary_type": summary_type,
        "summary_style": summary_style,
        "title_style": title_style,
    }

# ═════════════════════════════════════════════════════════════
# 每步 mock 输出数据（模拟真实 AI 返回结构）
# ═════════════════════════════════════════════════════════════

MOCK_STEP_OUTPUTS: Dict[str, Dict[str, Any]] = {
    "clean": {
        "cleaned_text": "近日，我国新能源汽车产业发展再传捷报。据中国汽车工业协会最新数据显示，今年前五个月，全国新能源汽车销量达到224.7万辆，同比增长46.8%，市场占有率达到27.7%。在技术创新方面，多家车企宣布在固态电池领域取得重大突破。",
        "original_length": 450,
        "cleaned_length": 128,
        "removed_patterns": ["HTML标签", "多余空行", "广告文本"],
    },
    "extract_keywords": {
        "keywords": [
            {"word": "新能源汽车", "weight": 0.95, "type": "核心主题"},
            {"word": "固态电池", "weight": 0.87, "type": "技术突破"},
            {"word": "销量增长", "weight": 0.82, "type": "市场表现"},
            {"word": "充电基础设施", "weight": 0.76, "type": "产业配套"},
            {"word": "市场占有率", "weight": 0.71, "type": "行业指标"},
        ],
        "total_extracted": 12,
    },
    "extract_elements": {
        "who": "中国汽车工业协会、多家新能源车企",
        "when": "今年前五个月（最新数据）",
        "where": "全国",
        "what": "新能源汽车销量224.7万辆，同比增长46.8%",
        "why": "技术创新（固态电池突破）+ 政策支持",
        "how": "固态电池能量密度突破500Wh/kg，充电设施达630万台",
        "confidence": 0.89,
    },
    "generate_title_summary": {
        "candidate_titles": [
            "新能源汽车前五月销量突破224万辆，固态电池技术取得重大突破",
            "同比增长46.8%！新能源汽车市场占有率攀升至27.7%",
            "固态电池能量密度突破500Wh/kg，纯电动车续航有望超1000公里",
        ],
        "summary_short": "今年前五个月，我国新能源汽车销量达224.7万辆，同比增长46.8%，市场占有率达27.7%。多家车企在固态电池领域取得突破，能量密度突破500Wh/kg。",
        "summary_long": "据中国汽车工业协会最新数据，今年前五个月全国新能源汽车销量达224.7万辆，同比增长46.8%，市场占有率达27.7%。在技术创新方面，固态电池能量密度已突破500Wh/kg，预计明年搭载于高端车型，续航里程将突破1000公里。充电基础设施累计达630万台，同比增长56%。业内预计全年销量有望突破500万辆，继续保持全球领先地位。",
        "selected_title_index": 0,
    },
    "match_topic": {
        "primary_topic": "新能源汽车产业",
        "secondary_topics": ["固态电池技术", "汽车工业", "清洁能源"],
        "confidence": 0.92,
        "topic_category": "科技/产业",
    },
    "judge_timeline": {
        "is_timely": True,
        "time_sensitivity": "high",
        "recommended_position": "头条/要闻区",
        "expiration_hours": 48,
        "reason": "涉及最新产业数据与技术突破，时效性强",
    },
    "check_consistency": {
        "risk_level": "low",
        "risk_label": "低风险",
        "title_summary_match": 0.94,
        "fact_check_results": [
            {"claim": "销量224.7万辆", "verdict": "与原文一致"},
            {"claim": "同比增长46.8%", "verdict": "与原文一致"},
            {"claim": "能量密度500Wh/kg", "verdict": "与原文一致"},
        ],
        "suggestions": [],
    },
    "edit_suggestions": {
        "overall_score": 87,
        "suggestions": [
            {
                "type": "标题优化",
                "priority": "medium",
                "detail": "建议在标题中加入「同比+46.8%」等关键数据以增强说服力",
                "reason": "数据驱动标题点击率更高",
            },
            {
                "type": "结构优化",
                "priority": "low",
                "detail": "可增加专家点评段落以提升深度",
                "reason": "行业分析类新闻读者期待多方观点",
            },
        ],
        "readability_score": 82,
    },
}


# ═════════════════════════════════════════════════════════════
# Mock 任务创建响应（与 schema.py AgentTaskResponse 一致）
# ═════════════════════════════════════════════════════════════

def generate_mock_task_response(task_id: Optional[int] = None) -> Dict[str, Any]:
    """生成模拟的任务创建响应。"""
    if task_id is None:
        task_id = random.randint(1000, 9999)
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "任务已创建（Mock 模式），正在排队等待处理",
    }


# ═════════════════════════════════════════════════════════════
# Mock 任务详情响应（与 schema.py AgentTaskDetailResponse 一致）
# ═════════════════════════════════════════════════════════════

def generate_mock_task_detail(
    task_id: int,
    current_step_index: int = 0,
    status: str = "running",
    pipeline_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """根据当前步骤索引生成模拟任务详情。

    Args:
        task_id: 任务 ID
        current_step_index: 当前已完成的步骤数 (0-8)
        status: 任务状态 (pending/running/completed/failed)
    """
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    steps = []
    for i, meta in enumerate(STEP_META_MOCK):
        step_status = "pending"
        if i < current_step_index:
            step_status = "completed"
        elif i == current_step_index and status == "running":
            step_status = "running"

        step_output = MOCK_STEP_OUTPUTS.get(meta["name"], {}) if step_status == "completed" else {}
        if meta["name"] == "generate_title_summary" and step_status == "completed":
            step_output = _build_mock_generate_output(
                input_text="",
                pipeline_params=pipeline_params or {},
            )

        steps.append({
            "id": i + 1,
            "task_id": task_id,
            "step_order": meta["order"],
            "step_name": meta["name"],
            "step_label": meta["label"],
            "status": step_status,
            "input_data": {} if i == 0 else MOCK_STEP_OUTPUTS.get(STEP_META_MOCK[i - 1]["name"], {}),
            "output_data": step_output,
            "llm_provider": "mock" if step_status == "completed" else None,
            "llm_model": "mock/gpt-4" if step_status == "completed" else None,
            "llm_request_tokens": random.randint(200, 800) if step_status == "completed" else 0,
            "llm_response_tokens": random.randint(100, 500) if step_status == "completed" else 0,
            "response_ms": random.randint(300, 2000) if step_status == "completed" else 0,
            "error_message": None,
            "retry_count": 0,
            "started_at": now if step_status in ("completed", "running") else None,
            "completed_at": now if step_status == "completed" else None,
            "created_at": now,
        })

    progress = int(current_step_index / 8 * 100) if status == "running" else (100 if status == "completed" else 0)

    result_json = None
    if status == "completed":
        result_json = [
            {"step": s["step_name"], "output": MOCK_STEP_OUTPUTS.get(s["step_name"], {})}
            for s in STEP_META_MOCK
        ]

    return {
        "id": task_id,
        "user_id": 0,
        "news_id": None,
        "task_type": "news_editor",
        "input_text": "",
        "cleaned_text": MOCK_STEP_OUTPUTS["clean"]["cleaned_text"] if current_step_index >= 1 else None,
        "status": status,
        "progress": progress,
        "current_step": STEP_META_MOCK[current_step_index]["name"] if 0 <= current_step_index < 8 else None,
        "result_json": result_json,
        "total_steps": 8,
        "completed_steps": current_step_index,
        "failed_step": None,
        "error_message": None,
        "started_at": now if status != "pending" else None,
        "completed_at": now if status == "completed" else None,
        "created_at": now,
        "updated_at": now,
        "steps": steps,
    }


# ═════════════════════════════════════════════════════════════
# Phase 2 升级：供前端 Phase 1/2 使用的便捷数据（保留向后兼容）
# ═════════════════════════════════════════════════════════════

def get_mock_steps_for_frontend() -> List[Dict[str, Any]]:
    """返回前端所需的完整 mock 步骤数据。

    Phase 2 注意：前端不再使用此数据进行客户端模拟。
    保留此函数供参考和其他模块使用。
    """
    return [
        {
            "name": meta["name"],
            "label": meta["label"],
            "order": meta["order"],
            "status": "pending",
            "output": MOCK_STEP_OUTPUTS.get(meta["name"], {}),
            "latency_ms": random.randint(300, 2000),
            "tokens": random.randint(100, 800),
            "provider": "mock",
            "model": "mock/gpt-4",
        }
        for meta in STEP_META_MOCK
    ]


# ═════════════════════════════════════════════════════════════
# Phase 2 升级：Active Mock 任务管理
# ═════════════════════════════════════════════════════════════

async def run_mock_task(
    user_id: int = 0,
    input_text: str = "",
    news_id: Optional[int] = None,
    task_type: str = "news_editor",
    pipeline_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """创建 mock 任务记录并启动 MockTaskRunner 后台状态机。

    流程：
    1. 写入 agent_task 记录（status=pending）
    2. 后台启动 MockTaskRunner → 逐步推进 8 步
    3. 立即返回 task_id + status

    前端拿到 task_id 后通过 polling GET /task/{id} 获取实时进度。
    """
    from app.modules.news_editor_agent.service import AgentService
    from app.modules.news_editor_agent.task_runner import schedule_mock_task

    # 使用 AgentService.create_task 创建任务记录（DB 或 Mock 存储）
    task_response = await AgentService.create_task(
        user_id=user_id,
        input_text=input_text,
        news_id=news_id,
        task_type=task_type,
    )

    # 后台启动 MockTaskRunner（非阻塞）
    schedule_mock_task(task_response.task_id, input_text, pipeline_params=pipeline_params)

    return {
        "task_id": task_response.task_id,
        "status": "running",
        "message": "Mock 任务已创建，后台状态机已启动",
    }


def get_mock_task_detail(task_id: int) -> Optional[Dict[str, Any]]:
    """从真实存储（DB/Mock）读取任务详情。

    与 AgentService.get_task_detail() 返回结构兼容，
    但返回原生 dict 而非 Pydantic 模型，方便直接序列化。
    """
    try:
        from app.modules.news_editor_agent.service import AgentService
        detail = AgentService.get_task_detail(task_id)
        return detail.model_dump() if hasattr(detail, 'model_dump') else detail
    except Exception:
        return None
