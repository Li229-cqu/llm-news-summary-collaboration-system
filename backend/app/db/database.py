from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import pymysql

from app.core.config import settings


def get_connection() -> pymysql.connections.Connection:
    """创建 MySQL 连接。"""
    return pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def execute_query(sql: str, params: Any | None = None) -> list[dict[str, Any]]:
    """执行查询并返回字典列表。"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        connection.close()


def execute_one(sql: str, params: Any | None = None) -> dict[str, Any] | None:
    """执行查询并返回单条结果。"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            row = cursor.fetchone()
            return dict(row) if row is not None else None
    finally:
        connection.close()


def execute_update(sql: str, params: Any | None = None) -> int:
    """执行更新语句并返回影响行数。"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            affected_rows = cursor.execute(sql, params or ())
        connection.commit()
        return affected_rows
    finally:
        connection.close()


def check_db_connection() -> bool:
    """执行 SELECT 1 检测数据库是否可达，返回 True/False。"""
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        finally:
            conn.close()
        return True
    except Exception:  # noqa: BLE001
        return False


def execute_insert(sql: str, params: Any | None = None) -> int:
    """执行插入语句并返回自增ID。"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            last_id = cursor.lastrowid
        connection.commit()
        return last_id
    finally:
        connection.close()

