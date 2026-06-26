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

    return AIGenerateResponse(
        candidate_titles=list(_load_json(row.get("candidate_titles"), [])),
        summary_short=str(row.get("summary_short") or ""),
        summary_long=str(row.get("summary_long") or ""),
        summary_points=list(_load_json(row.get("summary_points"), [])),
        keywords=list(_load_json(row.get("keywords"), [])),
        elements=NewsElement(**elements_raw),
        consistency=ConsistencyCheck(**consistency_raw),
    )


async def _call_ai_service(request: AIGenerateRequest) -> AIGenerateResponse:
    endpoint = f"{settings.ai_service_url.rstrip('/')}/ai/generate-title-summary"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(endpoint, json=request.model_dump())
            response.raise_for_status()
            payload = response.json()
    except (httpx.RequestError, httpx.HTTPStatusError, httpx.TimeoutException) as exc:
        raise AppException(code=503, message=AI_SERVICE_UNAVAILABLE_MESSAGE) from exc

    if payload.get("code") != 200:
        raise AppException(
            code=payload.get("code", 503),
            message=payload.get("message", AI_SERVICE_UNAVAILABLE_MESSAGE),
        )

    try:
        return AIGenerateResponse(**payload["data"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AppException(code=503, message=AI_SERVICE_UNAVAILABLE_MESSAGE) from exc


def _save_ai_record(
    request: AIGenerateRequest,
    result: AIGenerateResponse,
    current_user: Optional[Any] = None,
) -> None:
    user_id = _get_user_id(current_user)
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
        "risk_level": result.consistency.risk_level,
        "check_result": _dump_json(result.consistency.model_dump()),
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
                news_elements, risk_level, check_result, created_at, updated_at, status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
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
    if user_id == 0:
        return None

    rows = execute_query(
        """
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
            created_at,
            status
        FROM ai_generate_record
        WHERE user_id = %s AND status = 1
        ORDER BY created_at DESC, id DESC
        """,
        [user_id],
    )
    if not rows:
        return None

    records: list[dict[str, Any]] = []
    for row in rows:
        records.append(
            {
                "id": row["id"],
                "source": row["source"],
                "source_news_id": row["source_news_id"],
                "source_title": row["source_title"],
                "title_count": row["title_count"],
                "risk_level": row["risk_level"] or "low",
                "created_at": _now_text() if row.get("created_at") is None else str(row["created_at"]),
            }
        )
    return records


def _query_ai_record_detail_from_db(
    record_id: Union[int, str],
    current_user: Optional[Any] = None,
) -> Optional[Dict[str, Any]]:
    user_id = _get_user_id(current_user)
    params: list[Any] = [record_id]
    where_clause = "id = %s"
    if user_id:
        where_clause += " AND user_id = %s"
        params.append(user_id)

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
    return {
        "id": row["id"],
        "source": row["source"],
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
        "result": result.model_dump(),
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

    result = await _call_ai_service(request)
    try:
        _save_ai_record(request, result, current_user=current_user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("AI 生成记录保存失败，继续返回结果：%s", exc)
    return result


def get_ai_records(current_user: Optional[Any] = None) -> list[AIGenerateRecordItem]:
    """获取 AI 生成记录列表，数据库优先，mock 兜底。"""
    rows = None
    try:
        rows = _query_ai_records_from_db(current_user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取 AI 生成记录数据库失败，回退 mock：%s", exc)

    if rows is not None:
        return [
            AIGenerateRecordItem(
                id=row["id"],
                source=row["source"],
                source_news_id=row["source_news_id"],
                source_title=row["source_title"],
                title_count=row["title_count"],
                risk_level=row["risk_level"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    all_records = get_all_records()
    user_id = _get_user_id(current_user)
    if user_id:
        all_records = [record for record in all_records if record.get("user_id", 0) == user_id]

    return [
        AIGenerateRecordItem(
            id=record["id"],
            source=record["source"],
            source_news_id=record.get("source_news_id"),
            source_title=record["source_title"],
            title_count=record["title_count"],
            risk_level=record["risk_level"],
            created_at=record["created_at"],
        )
        for record in all_records
    ]


def get_ai_record_detail(
    record_id: Union[int, str],
    current_user: Optional[Any] = None,
) -> AIGenerateRecordDetail:
    """获取 AI 生成记录详情，数据库优先，mock 兜底。"""
    try:
        row = _query_ai_record_detail_from_db(record_id, current_user=current_user)
        if row is not None:
            return AIGenerateRecordDetail(**row)
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取 AI 生成记录详情失败，回退 mock：%s", exc)

    record = get_record_by_id(record_id)
    if not record:
        raise AppException(code=404, message="历史记录不存在")

    return AIGenerateRecordDetail(
        id=record["id"],
        source=record["source"],
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
