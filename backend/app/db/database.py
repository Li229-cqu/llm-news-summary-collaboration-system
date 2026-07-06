from __future__ import annotations

import logging
import threading
from typing import Any

import pymysql
from dbutils.pooled_db import PooledDB

from app.core.config import settings

logger = logging.getLogger(__name__)

_pool_lock = threading.Lock()
_connection_pool: PooledDB | None = None
_pool_init_error: Exception | None = None


def _build_connection_pool() -> PooledDB:
    """Create the shared MySQL connection pool."""
    return PooledDB(
        creator=pymysql,
        mincached=1,
        maxcached=5,
        maxconnections=10,
        blocking=True,
        ping=1,
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def _get_connection_pool() -> PooledDB:
    """Lazily initialize the connection pool and surface initialization errors."""
    global _connection_pool, _pool_init_error

    if _connection_pool is not None:
        return _connection_pool

    if _pool_init_error is not None:
        raise RuntimeError("数据库连接池初始化失败，请检查数据库配置") from _pool_init_error

    with _pool_lock:
        if _connection_pool is not None:
            return _connection_pool

        if _pool_init_error is not None:
            raise RuntimeError("数据库连接池初始化失败，请检查数据库配置") from _pool_init_error

        try:
            _connection_pool = _build_connection_pool()
            logger.info(
                "数据库连接池初始化成功：%s@%s:%s/%s",
                settings.db_user,
                settings.db_host,
                settings.db_port,
                settings.db_name,
            )
        except Exception as exc:  # noqa: BLE001
            _pool_init_error = exc
            logger.exception("数据库连接池初始化失败")
            raise RuntimeError("数据库连接池初始化失败，请检查数据库配置") from exc

    if _connection_pool is None:
        raise RuntimeError("数据库连接池初始化失败，请检查数据库配置")
    return _connection_pool


def get_connection() -> pymysql.connections.Connection:
    """Get a pooled MySQL connection.

    The returned object's close() method returns the connection to the pool.
    """
    conn = _get_connection_pool().connection()
    # 确保连接使用 UTF-8 编码
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
    except Exception:  # noqa: BLE001
        pass
    return conn


def execute_query(sql: str, params: Any | None = None) -> list[dict[str, Any]]:
    """Execute a query and return a list of dictionaries."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params if params is not None else ())
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        connection.close()


def execute_one(sql: str, params: Any | None = None) -> dict[str, Any] | None:
    """Execute a query and return the first row."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params if params is not None else ())
            row = cursor.fetchone()
            return dict(row) if row is not None else None
    finally:
        connection.close()


def execute_update(sql: str, params: Any | None = None) -> int:
    """Execute an update statement and return the affected row count."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            affected_rows = cursor.execute(sql, params if params is not None else ())
        connection.commit()
        return affected_rows
    finally:
        connection.close()


def execute_insert(sql: str, params: Any | None = None) -> int:
    """Execute an insert statement and return the last inserted id."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params if params is not None else ())
            last_id = cursor.lastrowid
        connection.commit()
        return last_id
    finally:
        connection.close()


def check_db_connection() -> bool:
    """Check whether the database is reachable."""
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


def clear_sensitive_system_config_values() -> int:
    """Remove sensitive rows from system_config without touching business tables."""
    return execute_update(
        """
        DELETE FROM system_config
        WHERE (
            REPLACE(REPLACE(REPLACE(LOWER(config_key), '_', ''), '-', ''), ' ', '') LIKE %s
            OR REPLACE(REPLACE(REPLACE(LOWER(config_key), '_', ''), '-', ''), ' ', '') LIKE %s
            OR LOWER(config_key) LIKE %s
        )
        """,
        ["%apikey%", "%secretkey%", "%token%"],
    )
