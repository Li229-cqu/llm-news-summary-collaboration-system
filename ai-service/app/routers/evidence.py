from fastapi import APIRouter
from typing import List, Dict

from app.common.response import ApiResponse, success_response
from app.core.config import settings
from app.schemas.evidence import EvidenceRequest, EvidenceResponse
from app.services.evidence_service import evaluate_evidence, evaluate_multisource_evidence, _detect_conflicts

router = APIRouter(prefix=settings.api_prefix, tags=["证据评估"])


@router.post("/evaluate-evidence", response_model=ApiResponse[EvidenceResponse])
async def evaluate(request: EvidenceRequest) -> ApiResponse[EvidenceResponse]:
    """
    评估摘要的证据链（双AI架构：智谱评估）。
    
    请求体：
    - summary_text: 摘要文本
    - original_text: 原文文本
    - news_id: 新闻ID（可选）
    
    返回：
    - evidence_chain: 证据链数据
    - risk_level: 风险等级（low/medium/high）
    - risk_details: 风险详情描述
    - source: 来源（mock/llm）
    """
    return success_response(evaluate_evidence(request))


class MultisourceEvidenceRequest(EvidenceRequest):
    other_news: List[Dict] = []


@router.post("/evaluate-multisource-evidence", response_model=ApiResponse[dict])
async def evaluate_multisource(request: EvidenceRequest, other_news: List[Dict] = None) -> ApiResponse[dict]:
    """
    多源新闻证据评估与冲突检测。
    
    请求体：
    - summary_text: 摘要文本
    - original_text: 主新闻原文
    - news_id: 主新闻ID
    - other_news: 其他来源新闻列表 [{"id": 1, "content": "...", "source_name": "..."}, ...]
    
    返回：
    - evidence_chain: 综合证据链数据
    - risk_level: 风险等级
    - conflicts: 冲突检测结果列表
    - conflict_count: 冲突数量
    """
    response = evaluate_multisource_evidence(request, other_news or [])
    
    conflicts = _detect_conflicts(response.evidence_chain)
    
    return success_response({
        "evidence_chain": response.evidence_chain.model_dump(),
        "risk_level": response.risk_level,
        "risk_details": response.risk_details,
        "evidence_coverage": response.evidence_chain.evidence_coverage,
        "conflicts": conflicts,
        "conflict_count": len(conflicts),
        "source": response.source,
    })


@router.post("/detect-conflicts", response_model=ApiResponse[dict])
async def detect_conflicts(request: EvidenceRequest, other_news: List[Dict] = None) -> ApiResponse[dict]:
    """
    检测多源新闻之间的信息冲突。
    
    请求体：
    - summary_text: 摘要文本
    - original_text: 主新闻原文
    - other_news: 其他来源新闻列表
    
    返回：
    - conflicts: 冲突列表
    - conflict_count: 冲突数量
    - conflict_types: 冲突类型统计
    """
    response = evaluate_multisource_evidence(request, other_news or [])
    conflicts = _detect_conflicts(response.evidence_chain)
    
    conflict_types = {}
    for conflict in conflicts:
        ctype = conflict.get("conflict_type", "other")
        conflict_types[ctype] = conflict_types.get(ctype, 0) + 1
    
    return success_response({
        "conflicts": conflicts,
        "conflict_count": len(conflicts),
        "conflict_types": conflict_types,
    })
