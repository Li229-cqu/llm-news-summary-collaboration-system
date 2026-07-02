from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import httpx

from app.common.exceptions import AppException
from app.core.config import settings
from app.db.database import execute_one, execute_query, execute_update
from app.mock.ai_records import add_record, delete_record, get_all_records, get_record_by_id
from app.modules.ai.schema import (
    AIGenerateRecordDetail,
    AIGenerateRecordItem,
    AIGenerateRequest,
    AIGenerateResponse,
    ConsistencyCheck,
    EvidenceChain,
    NewsElement,
)

logger = logging.getLogger(__name__)

AI_SERVICE_UNAVAILABLE_MESSAGE = "AI 服务暂时不可用，请稍后重试"


def _get_user_id(current_user: Optional[Any] = None) -> int:
    if current_user is None:
        return 0
    if isinstance(current_user, dict):
        return int(current_user.get("id") or 0)
    return int(getattr(current_user, "id", 0) or 0)


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _load_json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return default
    return default


def _normalize_record_source(value: Any) -> str:
    return str(value or "manual") if str(value or "manual") in {"manual", "news"} else "manual"


def _normalize_risk_level(value: Any) -> str:
    return str(value or "low") if str(value or "low") in {"low", "medium", "high"} else "low"


def _normalize_ai_source(value: Any) -> str:
    return str(value or "mock") if str(value or "mock") in {"mock", "llm", "demo"} else "mock"


def _build_result_from_row(row: dict[str, Any]) -> AIGenerateResponse:
    elements_raw = _load_json(
        row.get("news_elements"),
        {
            "who": "",
            "what": "",
            "when": "",
            "where": "",
            "why": "",
            "how": "",
        },
    )
    if not isinstance(elements_raw, dict):
        elements_raw = {
            "who": "",
            "what": "",
            "when": "",
            "where": "",
            "why": "",
            "how": "",
        }

    consistency_raw = _load_json(
        row.get("check_result"),
        {
            "score": 0,
            "risk_level": "low",
            "issues": [],
            "suggestions": [],
        },
    )
    if not isinstance(consistency_raw, dict):
        consistency_raw = {
            "score": 0,
            "risk_level": "low",
            "issues": [],
            "suggestions": [],
        }
    if isinstance(consistency_raw.get("consistency"), dict):
        consistency_raw = consistency_raw["consistency"]
    consistency_raw.setdefault("score", 0)
    consistency_raw.setdefault("issues", [])
    consistency_raw.setdefault("suggestions", [])
    consistency_raw["risk_level"] = _normalize_risk_level(consistency_raw.get("risk_level"))

    evidence_chain_raw = _load_json(row.get("evidence_json"), None)

    return AIGenerateResponse(
        candidate_titles=list(_load_json(row.get("candidate_titles"), [])),
        summary_short=str(row.get("summary_short") or ""),
        summary_long=str(row.get("summary_long") or ""),
        summary_points=list(_load_json(row.get("summary_points"), [])),
        keywords=list(_load_json(row.get("keywords"), [])),
        elements=NewsElement(**elements_raw),
        consistency=ConsistencyCheck(**consistency_raw),
        source=_normalize_ai_source(row.get("ai_source")),
        evidence_chain=EvidenceChain(**evidence_chain_raw) if evidence_chain_raw else None,
        risk_level=_normalize_risk_level(row.get("risk_level") or consistency_raw.get("risk_level", "low")),
        risk_details=row.get("risk_details") or "",
        evidence_coverage=row.get("evidence_coverage") or 0.0,
    )


async def _call_ai_service(request: AIGenerateRequest) -> AIGenerateResponse:
    endpoint = f"{settings.ai_service_url.rstrip('/')}/ai/generate-title-summary"
    logger.info(f"🚀 [REAL API] 调用 AI 服务: {endpoint}")
    logger.info(f"📋 [REAL API] 请求参数: input_text长度={len(request.input_text)}, title_count={request.title_count}")
    try:
        async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
            response = await client.post(endpoint, json=request.model_dump())
            logger.info(f"📡 [REAL API] 响应状态码: {response.status_code}")
            response.raise_for_status()
            payload = response.json()
        logger.info("✅ [REAL API] AI 服务调用成功")
    except httpx.TimeoutException as exc:
        logger.error(f"❌ [REAL API] AI 服务调用超时: {str(exc)}")
        raise AppException(code=503, message=AI_SERVICE_UNAVAILABLE_MESSAGE) from exc
    except httpx.HTTPStatusError as exc:
        logger.error(f"❌ [REAL API] AI 服务返回错误状态码: {exc.response.status_code}, 响应内容: {exc.response.text[:500]}")
        raise AppException(code=503, message=AI_SERVICE_UNAVAILABLE_MESSAGE) from exc
    except httpx.RequestError as exc:
        logger.error(f"❌ [REAL API] AI 服务网络请求失败: {type(exc).__name__}: {str(exc)}")
        raise AppException(code=503, message=AI_SERVICE_UNAVAILABLE_MESSAGE) from exc

    if payload.get("code") != 200:
        logger.error(f"❌ [REAL API] AI 服务返回错误: {payload.get('message')}")
        raise AppException(
            code=payload.get("code", 503),
            message=payload.get("message", AI_SERVICE_UNAVAILABLE_MESSAGE),
        )

    try:
        logger.info("✅ [REAL API] AI 生成结果解析成功")
        return AIGenerateResponse(**payload["data"])
    except (KeyError, TypeError, ValueError) as exc:
        logger.error(f"❌ [REAL API] AI 生成结果解析失败: {str(exc)}")
        raise AppException(code=503, message=AI_SERVICE_UNAVAILABLE_MESSAGE) from exc


import uuid
import asyncio

async_tasks: Dict[str, Dict[str, Any]] = {}


async def _create_async_task(request: AIGenerateRequest, current_user: Optional[Any] = None) -> str:
    task_id = str(uuid.uuid4())
    async_tasks[task_id] = {
        "status": "pending",
        "request": request,
        "result": None,
        "error": None,
    }
    
    async def execute_task():
        task = async_tasks.get(task_id)
        if not task:
            return
        
        try:
            async_tasks[task_id]["status"] = "running"
            result = await _call_ai_service(request)
            async_tasks[task_id]["status"] = "completed"
            async_tasks[task_id]["result"] = result
            
            try:
                _save_ai_record(request, result, current_user=current_user)
            except Exception as exc:
                logger.warning("AI 生成记录保存失败：%s", exc)
                
        except Exception as exc:
            async_tasks[task_id]["status"] = "failed"
            async_tasks[task_id]["error"] = str(exc)
            logger.error(f"❌ 异步任务 {task_id} 执行失败: {str(exc)}")
    
    asyncio.create_task(execute_task())
    return task_id


async def _get_async_task_result(task_id: str) -> Dict[str, Any]:
    task = async_tasks.get(task_id)
    if not task:
        raise AppException(code=404, message="任务不存在")
    
    result_data = {
        "task_id": task_id,
        "status": task["status"],
    }
    
    if task["status"] == "completed" and task["result"]:
        result_data["result"] = task["result"]
    elif task["status"] == "failed" and task["error"]:
        result_data["error"] = task["error"]
    
    return result_data


def _save_ai_record(
    request: AIGenerateRequest,
    result: AIGenerateResponse,
    current_user: Optional[Any] = None,
    response_ms: int = 0,
) -> None:
    user_id = _get_user_id(current_user)
    evidence_chain_json = _dump_json(result.evidence_chain.model_dump()) if result.evidence_chain else None
    evidence_status = 1 if result.evidence_chain else 0
    risk_level_value = result.risk_level if result.risk_level else result.consistency.risk_level
    risk_details_value = result.risk_details or ""
    evidence_coverage_value = result.evidence_coverage or 0.0
    
    record_payload = {
        "user_id": user_id,
        "source": request.source,
        "source_news_id": request.source_news_id,
        "source_title": request.source_title or "",
        "input_text": request.input_text,
        "title_count": request.title_count,
        "summary_type": request.summary_type,
        "summary_style": request.summary_style,
        "title_style": request.title_style,
        "summary_length": request.summary_length,
        "candidate_titles": _dump_json(result.candidate_titles),
        "summary_short": result.summary_short,
        "summary_long": result.summary_long,
        "summary_points": _dump_json(result.summary_points),
        "keywords": _dump_json(result.keywords),
        "news_elements": _dump_json(result.elements.model_dump()),
        "risk_level": risk_level_value,
        "check_result": _dump_json(result.consistency.model_dump()),
        "ai_source": result.source or "mock",
        "response_ms": response_ms,
        "evidence_json": evidence_chain_json,
        "evidence_status": evidence_status,
        "risk_details": risk_details_value,
        "evidence_coverage": evidence_coverage_value,
        "created_at": _now_text(),
        "updated_at": _now_text(),
        "status": 1,
    }

    try:
        execute_update(
            """
            INSERT INTO ai_generate_record (
                user_id, source, source_news_id, source_title, input_text, title_count, summary_type,
                summary_style, title_style, summary_length, candidate_titles,
                summary_short, summary_long, summary_points, keywords,
                news_elements, risk_level, check_result, ai_source, response_ms,
                evidence_json, evidence_status, risk_details, evidence_coverage,
                created_at, updated_at, status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s
            )
            """,
            [
                record_payload["user_id"],
                record_payload["source"],
                record_payload["source_news_id"],
                record_payload["source_title"],
                record_payload["input_text"],
                record_payload["title_count"],
                record_payload["summary_type"],
                record_payload["summary_style"],
                record_payload["title_style"],
                record_payload["summary_length"],
                record_payload["candidate_titles"],
                record_payload["summary_short"],
                record_payload["summary_long"],
                record_payload["summary_points"],
                record_payload["keywords"],
                record_payload["news_elements"],
                record_payload["risk_level"],
                record_payload["check_result"],
                record_payload["ai_source"],
                record_payload["response_ms"],
                record_payload["evidence_json"],
                record_payload["evidence_status"],
                record_payload["risk_details"],
                record_payload["evidence_coverage"],
                record_payload["created_at"],
                record_payload["updated_at"],
                record_payload["status"],
            ],
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("AI 生成记录写入数据库失败，回退 mock：%s", exc)
        add_record(
            {
                "user_id": user_id,
                "source": request.source,
                "source_news_id": request.source_news_id,
                "source_title": request.source_title or "",
                "input_text": request.input_text,
                "params": {
                    "title_count": request.title_count,
                    "summary_type": request.summary_type,
                    "summary_style": request.summary_style,
                    "title_style": request.title_style,
                    "summary_length": request.summary_length,
                },
                "result": result.model_dump(),
                "created_at": record_payload["created_at"],
                "title_count": request.title_count,
                "risk_level": result.consistency.risk_level,
            }
        )


def _query_ai_records_from_db(current_user: Optional[Any] = None) -> list[dict[str, Any]] | None:
    user_id = _get_user_id(current_user)
    
    if user_id is not None:
        if user_id > 0:
            params = [user_id]
        else:
            params = [1]
        where_clause = "user_id = %s AND status = 1"
    else:
        return None

    rows = execute_query(
        f"""
        SELECT
            id,
            user_id,
            source,
            source_news_id,
            source_title,
            input_text,
            title_count,
            summary_type,
            summary_style,
            title_style,
            summary_length,
            candidate_titles,
            summary_short,
            summary_long,
            summary_points,
            keywords,
            news_elements,
            risk_level,
            check_result,
            ai_source,
            evidence_json,
            evidence_status,
            risk_details,
            evidence_coverage,
            created_at,
            status
        FROM ai_generate_record
        WHERE {where_clause}
        ORDER BY created_at DESC, id DESC
        """,
        params,
    )
    if not rows:
        return None

    records: list[dict[str, Any]] = []
    for row in rows:
        records.append(
            {
                "id": row["id"],
                "source": _normalize_record_source(row.get("source")),
                "source_news_id": row["source_news_id"],
                "source_title": row["source_title"],
                "title_count": row["title_count"],
                "risk_level": _normalize_risk_level(row.get("risk_level")),
                "ai_source": _normalize_ai_source(row.get("ai_source")),
                "created_at": _now_text() if row.get("created_at") is None else str(row["created_at"]),
                "candidate_titles": _load_json(row.get("candidate_titles"), []),
                "summary_short": str(row.get("summary_short") or ""),
            }
        )
    return records


def _query_ai_record_detail_from_db(
    record_id: Union[int, str],
    current_user: Optional[Any] = None,
) -> Optional[Dict[str, Any]]:
    user_id = _get_user_id(current_user)
    params: list[Any] = [record_id]
    where_clause = "id = %s AND status = 1"

    row = execute_one(
        f"""
        SELECT
            id,
            user_id,
            source,
            source_news_id,
            source_title,
            input_text,
            title_count,
            summary_type,
            summary_style,
            title_style,
            summary_length,
            candidate_titles,
            summary_short,
            summary_long,
            summary_points,
            keywords,
            news_elements,
            risk_level,
            check_result,
            ai_source,
            evidence_json,
            evidence_status,
            risk_details,
            evidence_coverage,
            created_at,
            status
        FROM ai_generate_record
        WHERE {where_clause}
        """,
        params,
    )
    if not row:
        return None

    result = _build_result_from_row(row)
    result.source = _normalize_ai_source(row.get("ai_source"))
    return {
        "id": row["id"],
        "source": _normalize_record_source(row.get("source")),
        "source_news_id": row["source_news_id"],
        "source_title": row["source_title"],
        "input_text": row["input_text"],
        "params": {
            "title_count": row["title_count"],
            "summary_type": row["summary_type"],
            "summary_style": row["summary_style"],
            "title_style": row["title_style"],
            "summary_length": row["summary_length"],
        },
        "result": result,
        "created_at": _now_text() if row.get("created_at") is None else str(row["created_at"]),
    }


def _delete_ai_record_from_db(record_id: Union[int, str], current_user: Optional[Any] = None) -> bool:
    user_id = _get_user_id(current_user)
    params: list[Any] = [record_id]
    where_clause = "id = %s"
    if user_id:
        where_clause += " AND user_id = %s"
        params.append(user_id)

    affected_rows = execute_update(
        f"DELETE FROM ai_generate_record WHERE {where_clause}",
        params,
    )
    return affected_rows > 0


async def generate_title_summary(
    request: AIGenerateRequest,
    current_user: Optional[Any] = None,
) -> AIGenerateResponse:
    """调用 ai-service 生成结果，并同步保存到数据库。"""
    if not request.input_text.strip():
        raise AppException(code=400, message="输入文本不能为空")

    if not 1 <= request.title_count <= 5:
        raise AppException(code=400, message="标题数量必须在 1-5 范围内")

    import time
    start_time = time.time()
    result = await _call_ai_service(request)
    response_ms = int((time.time() - start_time) * 1000)
    
    try:
        _save_ai_record(request, result, current_user=current_user, response_ms=response_ms)
    except Exception as exc:  # noqa: BLE001
        logger.warning("AI 生成记录保存失败，继续返回结果：%s", exc)
    return result


def get_ai_records(current_user: Optional[Any] = None) -> list[AIGenerateRecordItem]:
    """获取 AI 生成记录列表，数据库优先，mock 兜底。"""
    rows = None
    user_id = _get_user_id(current_user)
    
    try:
        rows = _query_ai_records_from_db(current_user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取 AI 生成记录数据库失败，回退 mock：%s", exc)

    if rows is not None:
        return [
            AIGenerateRecordItem(
                id=row["id"],
                source=_normalize_record_source(row.get("source")),
                source_news_id=row["source_news_id"],
                source_title=row["source_title"],
                title_count=row["title_count"],
                risk_level=_normalize_risk_level(row.get("risk_level")),
                ai_source=_normalize_ai_source(row.get("ai_source")),
                created_at=row["created_at"],
                candidate_titles=row.get("candidate_titles", []),
                summary_short=row.get("summary_short", ""),
            )
            for row in rows
        ]

    all_records = get_all_records()
    if user_id is not None:
        if user_id > 0:
            all_records = [record for record in all_records if record.get("user_id", 0) == user_id]
        else:
            all_records = [record for record in all_records if record.get("user_id", 0) == 1]
    
    return [
        AIGenerateRecordItem(
            id=record["id"],
            source=_normalize_record_source(record.get("source")),
            source_news_id=record.get("source_news_id"),
            source_title=record["source_title"],
            title_count=record["title_count"],
            risk_level=_normalize_risk_level(record.get("risk_level")),
            created_at=record["created_at"],
            candidate_titles=record.get("result", {}).get("candidate_titles", []),
            summary_short=record.get("result", {}).get("summary_short", ""),
        )
        for record in all_records
    ]


def get_ai_record_detail(
    record_id: Union[int, str],
    current_user: Optional[Any] = None,
) -> AIGenerateRecordDetail:
    """获取 AI 生成记录详情，数据库优先，mock 兜底。"""
    user_id = _get_user_id(current_user)
    
    try:
        row = _query_ai_record_detail_from_db(record_id, current_user=current_user)
        if row is not None:
            return AIGenerateRecordDetail(**row)
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取 AI 生成记录详情失败，回退 mock：%s", exc)

    mock_user_id = user_id if user_id > 0 else 1
    record = get_record_by_id(record_id, user_id=mock_user_id)
    if not record:
        raise AppException(code=404, message="历史记录不存在")

    return AIGenerateRecordDetail(
        id=record["id"],
        source=_normalize_record_source(record.get("source")),
        source_news_id=record.get("source_news_id"),
        source_title=record["source_title"],
        input_text=record["input_text"],
        params=record["params"],
        result=AIGenerateResponse(**record["result"]),
        created_at=record["created_at"],
    )


def delete_ai_record(record_id: Union[int, str], current_user: Optional[Any] = None) -> bool:
    """删除 AI 生成记录，数据库优先，mock 兜底。"""
    try:
        if _delete_ai_record_from_db(record_id, current_user=current_user):
            return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("删除 AI 生成记录失败，回退 mock：%s", exc)
    return delete_record(record_id)


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """从上传的文件中提取文本内容。"""
    lower_name = filename.lower()
    
    if lower_name.endswith(".txt") or lower_name.endswith(".md"):
        try:
            return file_content.decode("utf-8")
        except UnicodeDecodeError:
            return file_content.decode("gbk", errors="ignore")
    
    elif lower_name.endswith(".docx"):
        try:
            from docx import Document
            from io import BytesIO
            doc = Document(BytesIO(file_content))
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            logger.warning("python-docx 未安装，无法解析 docx 文件")
            return "无法解析 docx 文件，请安装 python-docx 依赖"
        except Exception as exc:
            logger.warning("解析 docx 文件失败：%s", exc)
            return "docx 文件解析失败"
    
    elif lower_name.endswith(".pdf"):
        try:
            from PyPDF2 import PdfReader
            from io import BytesIO
            reader = PdfReader(BytesIO(file_content))
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        except ImportError:
            logger.warning("PyPDF2 未安装，无法解析 pdf 文件")
            return "无法解析 pdf 文件，请安装 PyPDF2 依赖"
        except Exception as exc:
            logger.warning("解析 pdf 文件失败：%s", exc)
            return "pdf 文件解析失败"
    
    else:
        raise AppException(code=400, message=f"不支持的文件格式：{filename}")


def handle_file_upload(file_content: bytes, filename: str) -> dict[str, Any]:
    """处理文件上传，提取文本内容。"""
    content = extract_text_from_file(file_content, filename)
    return {
        "success": True,
        "message": "文件上传成功",
        "content": content,
        "filename": filename,
    }
