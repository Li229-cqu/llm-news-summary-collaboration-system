from __future__ import annotations

import re
import json
import logging

from typing import Optional

HAS_SBERT = False
MODEL = None

try:
    from sentence_transformers import SentenceTransformer, util
    HAS_SBERT = True
except ImportError:
    HAS_SBERT = False

from app.common.exceptions import AIServiceException
from app.core.config import settings
from app.schemas.evidence import (
    EvidenceRequest,
    EvidenceResponse,
    EvidenceChain,
    SentenceEvidence,
    EvidenceItem,
)
from app.services.llm_client import call_evidence_llm

logger = logging.getLogger(__name__)


def _get_sbert_model():
    """获取 Sentence-BERT 模型（不自动下载）。"""
    global MODEL
    if MODEL is None and HAS_SBERT:
        try:
            MODEL = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)
            logger.info("Sentence-BERT 模型加载成功")
        except Exception as e:
            logger.info(f"本地 Sentence-BERT 模型不可用，使用简单相似度计算: {str(e)}")
            MODEL = False
    return MODEL if MODEL is not False else None


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r'[。！？；\n]+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _calculate_similarity(text1: str, text2: str) -> float:
    """语义相似度计算（优先使用 Sentence-BERT）。"""
    if not text1 or not text2:
        return 0.0
    
    model = _get_sbert_model()
    if model is not None:
        try:
            emb1 = model.encode(text1, convert_to_tensor=True)
            emb2 = model.encode(text2, convert_to_tensor=True)
            cosine_score = util.cos_sim(emb1, emb2)
            return float(cosine_score[0][0])
        except Exception as e:
            logger.warning(f"Sentence-BERT 相似度计算失败，降级为字符匹配: {str(e)}")
    
    common = 0
    text1_set = set(text1)
    for c in text2:
        if c in text1_set:
            common += 1
    
    if not text1 or not text2:
        return 0.0
    
    return common / len(text1_set.union(text2)) if len(text1_set.union(text2)) > 0 else 0.0


def _validate_evidence(summary_sentence: str, evidence_text: str, original_text: str) -> dict:
    is_valid = evidence_text in original_text
    
    similarity = _calculate_similarity(summary_sentence, evidence_text)
    
    return {
        "is_valid": is_valid,
        "similarity": round(similarity, 2),
    }


def _calculate_risk_level(evidence_chain: EvidenceChain, summary_type: str = "generate") -> tuple[str, str]:
    sentences = evidence_chain.sentences
    
    if not sentences:
        return "high", "无摘要内容"
    
    total_sentences = len(sentences)
    
    sentences_with_evidence = sum(1 for s in sentences if s.has_evidence and len(s.evidence) > 0)
    sentences_with_high_confidence = sum(
        1 for s in sentences 
        if s.has_evidence and 
        any(e.confidence >= 50 for e in s.evidence)
    )
    
    coverage_rate = sentences_with_evidence / total_sentences
    high_confidence_rate = sentences_with_high_confidence / total_sentences
    evidence_chain.evidence_coverage = coverage_rate
    
    if summary_type == "extract":
        if coverage_rate >= 0.9:
            return "low", f"证据充分，覆盖率: {coverage_rate:.1%}"
        elif coverage_rate >= 0.7:
            return "medium", f"部分内容缺乏证据，覆盖率: {coverage_rate:.1%}"
        else:
            return "high", f"高风险：证据覆盖率仅 {coverage_rate:.1%}"
    else:
        if coverage_rate >= 0.5:
            return "low", f"证据充分，覆盖率: {coverage_rate:.1%}"
        elif coverage_rate >= 0.3:
            return "medium", f"部分内容证据较弱，覆盖率: {coverage_rate:.1%}"
        elif coverage_rate >= 0.1:
            return "medium", f"证据覆盖率一般，建议核实关键信息，覆盖率: {coverage_rate:.1%}"
        else:
            return "medium", f"生成型摘要包含扩展内容，建议关注核心信息，覆盖率: {coverage_rate:.1%}"


def _build_evidence_prompt(request: EvidenceRequest) -> str:
    sentences = _split_sentences(request.summary_text)
    sentences_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(sentences)])
    
    prompt = f"""请为以下摘要中的每句话匹配原文证据，并评估匹配置信度。

摘要文本：
{sentences_text}

原文来源：
{request.original_text}

要求：
1. 为摘要中的每句话找到对应的原文片段
2. 如果一句话综合了多个来源，列出所有相关来源
3. 如果无法找到对应证据，明确标注"无证据"
4. 评估匹配置信度（0-100分），分数越高表示匹配越准确
5. 输出必须严格遵循指定的JSON格式

输出格式（JSON）：
{{
  "sentences": [
    {{
      "text": "[摘要句子1]",
      "evidence": [
        {{
          "news_id": {request.news_id},
          "source_name": "来源名称",
          "text": "[原文片段]",
          "position": "第X段",
          "confidence": 95
        }}
      ],
      "has_evidence": true
    }}
  ]
}}

【字段规则】
- has_evidence 必须是布尔值
- confidence 必须是 0-100 之间的整数
- evidence 数组可以为空（当 has_evidence 为 false 时）
- 原文片段必须是从原文中直接截取的内容
- position 格式为"第X段"或"第X行"

【开始评估】
请直接返回 JSON，不要其他内容。
"""
    return prompt


def evaluate_evidence_mock(request: EvidenceRequest) -> EvidenceResponse:
    sentences = _split_sentences(request.summary_text)
    original_sentences = _split_sentences(request.original_text)
    
    sentence_evidences = []
    
    if request.summary_type == "generate":
        original_text = request.original_text
        original_chars = set(original_text)
        
        for idx, sentence in enumerate(sentences):
            sentence_chars = set(sentence)
            common_chars = sentence_chars & original_chars
            
            if len(common_chars) >= 3:
                best_fragment = original_sentences[0][:80] if original_sentences else ""
                evidence_item = EvidenceItem(
                    news_id=request.news_id,
                    source_name="智能证据匹配",
                    text=best_fragment,
                    position=f"第{idx+1}段",
                    confidence=50,
                    similarity=0.0,
                )
                
                sentence_evidences.append(SentenceEvidence(
                    text=sentence,
                    evidence=[evidence_item],
                    has_evidence=True,
                    risk_level=0,
                ))
            else:
                sentence_evidences.append(SentenceEvidence(
                    text=sentence,
                    evidence=[],
                    has_evidence=False,
                    risk_level=1,
                ))
    else:
        for i, sentence in enumerate(sentences):
            matched = False
            max_similarity = 0.0
            best_fragment = ""
            
            for j, original_sentence in enumerate(original_sentences):
                similarity = _calculate_similarity(sentence, original_sentence)
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_fragment = original_sentence[:80]
                    if similarity >= 0.3:
                        matched = True
                        break
            
            if matched and max_similarity >= 0.3:
                evidence_item = EvidenceItem(
                    news_id=request.news_id,
                    source_name="智能证据匹配",
                    text=best_fragment,
                    position=f"第{i+1}段",
                    confidence=int(max_similarity * 100),
                    similarity=round(max_similarity, 2),
                )
                
                sentence_evidences.append(SentenceEvidence(
                    text=sentence,
                    evidence=[evidence_item],
                    has_evidence=True,
                    risk_level=0 if max_similarity >= 0.6 else 1,
                ))
            else:
                sentence_evidences.append(SentenceEvidence(
                    text=sentence,
                    evidence=[],
                    has_evidence=False,
                    risk_level=2,
                ))
    
    evidence_chain = EvidenceChain(sentences=sentence_evidences)
    risk_level, risk_details = _calculate_risk_level(evidence_chain, request.summary_type)
    
    return EvidenceResponse(
        evidence_chain=evidence_chain,
        risk_level=risk_level,
        risk_details=risk_details,
        source="mock",
    )


async def evaluate_evidence(request: EvidenceRequest) -> EvidenceResponse:
    if not request.summary_text.strip():
        raise AIServiceException(code=400, message="摘要文本不能为空")
    
    if not request.original_text.strip():
        raise AIServiceException(code=400, message="原文文本不能为空")
    
    if not settings.evidence_llm_enabled:
        logger.info("证据评估 LLM 未启用，使用 mock 生成响应")
        return evaluate_evidence_mock(request)
    
    logger.info("证据评估 LLM 已启用，准备调用智谱 GLM")
    
    try:
        prompt = _build_evidence_prompt(request)
        messages = [{"role": "user", "content": prompt}]
        
        llm_response = await call_evidence_llm(messages)
        
        try:
            json_str = llm_response.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:-3].strip()
            elif json_str.startswith('```'):
                json_str = json_str[3:-3].strip()
            
            data = json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"证据评估 JSON 解析失败，fallback 到 mock: {str(e)}")
            return evaluate_evidence_mock(request)
        
        sentences_data = data.get("sentences", [])
        
        sentence_evidences = []
        for sent_data in sentences_data:
            evidence_items = []
            for ev_data in sent_data.get("evidence", []):
                validate_result = _validate_evidence(
                    sent_data.get("text", ""),
                    ev_data.get("text", ""),
                    request.original_text,
                )
                
                evidence_items.append(EvidenceItem(
                    news_id=ev_data.get("news_id", request.news_id),
                    source_name=ev_data.get("source_name", "unknown"),
                    text=ev_data.get("text", ""),
                    position=ev_data.get("position", ""),
                    confidence=int((ev_data.get("confidence", 0) * 0.6 + validate_result["similarity"] * 100 * 0.4)),
                    similarity=validate_result["similarity"],
                ))
            
            has_evidence = sent_data.get("has_evidence", len(evidence_items) > 0)
            
            max_confidence = max(e.confidence for e in evidence_items) if evidence_items else 0
            risk_level = 0 if max_confidence >= 60 else (1 if max_confidence > 0 else 2)
            
            sentence_evidences.append(SentenceEvidence(
                text=sent_data.get("text", ""),
                evidence=evidence_items,
                has_evidence=has_evidence,
                risk_level=risk_level,
            ))
        
        evidence_chain = EvidenceChain(sentences=sentence_evidences)
        risk_level, risk_details = _calculate_risk_level(evidence_chain, request.summary_type)
        
        return EvidenceResponse(
            evidence_chain=evidence_chain,
            risk_level=risk_level,
            risk_details=risk_details,
            source="llm",
        )
    
    except Exception as e:
        logger.warning(f"证据评估 LLM 调用失败，fallback 到 mock: {type(e).__name__}: {str(e)}")
        return evaluate_evidence_mock(request)


def _detect_conflicts(evidence_chain: EvidenceChain) -> list[dict]:
    conflicts = []
    
    for i, sentence1 in enumerate(evidence_chain.sentences):
        for j, sentence2 in enumerate(evidence_chain.sentences):
            if i >= j:
                continue
            
            if sentence1.evidence and sentence2.evidence:
                for ev1 in sentence1.evidence:
                    for ev2 in sentence2.evidence:
                        if ev1.news_id != ev2.news_id:
                            similarity = _calculate_similarity(ev1.text, ev2.text)
                            
                            if similarity < 0.5:
                                conflicts.append({
                                    "sentence1": sentence1.text[:30],
                                    "sentence2": sentence2.text[:30],
                                    "evidence1": ev1.text[:50],
                                    "evidence2": ev2.text[:50],
                                    "news1_id": ev1.news_id,
                                    "news2_id": ev2.news_id,
                                    "similarity": round(similarity, 2),
                                    "conflict_type": "description",
                                })
    
    return conflicts


def evaluate_multisource_evidence(request: EvidenceRequest, other_news: list[dict] = None) -> EvidenceResponse:
    response = evaluate_evidence(request)
    
    if other_news:
        conflicts = _detect_conflicts(response.evidence_chain)
        for news in other_news:
            additional_request = EvidenceRequest(
                summary_text=request.summary_text,
                original_text=news.get("content", ""),
                news_id=news.get("id", 0),
            )
            additional_response = evaluate_evidence(additional_request)
            
            for sent in additional_response.evidence_chain.sentences:
                for existing_sent in response.evidence_chain.sentences:
                    if sent.text == existing_sent.text:
                        existing_sent.evidence.extend(sent.evidence)
    
    return response
