#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""M12 Analytics Demo Data Cleaner

清理所有 M12_DEMO / M12_TEST 标记的演示数据。
仅删除标记字段中包含 M12_DEMO 或 M12_TEST 的行，不清空整张表，不影响真实业务数据。

Usage:
  cd backend
  .venv\Scripts\python.exe ../scripts/clean_m12_analytics_demo.py

Safety:
  - 不对任何表使用 TRUNCATE 或无条件 DELETE。
  - 不删除 admin/editor/user 基础账号。
  - 使用 LIKE '%M12_DEMO%' 或 LIKE '%M12_TEST%' 精确匹配。
  - 执行前打印确认信息和预计影响行数。
  - 需要用户确认后才执行。
"""

from __future__ import annotations

import sys

import pymysql

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "llm_news_user",
    "password": "123456",
    "database": "llm_news_system",
    "charset": "utf8mb4",
}

MARKERS = ["M12_DEMO", "M12_TEST"]


def conn() -> pymysql.connections.Connection:
    return pymysql.connect(**DB_CONFIG)


def _like_clause(column: str) -> str:
    """Build a LIKE clause covering all markers for a column."""
    parts = " OR ".join(f"{column} LIKE '%{m}%'" for m in MARKERS)
    return f"({parts})"


def _count(db: pymysql.connections.Connection, table: str, where: str) -> int:
    with db.cursor() as c:
        c.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}")
        row = c.fetchone()
        return row[0] if row else 0


def _delete(db: pymysql.connections.Connection, table: str, where: str) -> int:
    with db.cursor() as c:
        c.execute(f"DELETE FROM {table} WHERE {where}")
        return c.rowcount


def main() -> None:
    print("=" * 60)
    print("M12 Analytics Demo Data Cleaner")
    print(f"Markers: {MARKERS}")
    print("=" * 60)

    db = conn()
    try:
        # ── Define cleanup rules ─────────────────────────────────
        # (table, where_clause, safe_label)
        rules: list[tuple[str, str, str]] = [
            (
                "news",
                _like_clause("title"),
                "title LIKE '%M12_DEMO%' OR title LIKE '%M12_TEST%'",
            ),
            (
                "community_post",
                _like_clause("title"),
                "title LIKE '%M12_DEMO%' OR title LIKE '%M12_TEST%'",
            ),
            (
                "news_comment",
                _like_clause("content"),
                "content LIKE '%M12_DEMO%' OR content LIKE '%M12_TEST%'",
            ),
            (
                "post_comment",
                _like_clause("content"),
                "content LIKE '%M12_DEMO%' OR content LIKE '%M12_TEST%'",
            ),
            (
                "ai_generate_record",
                f"({_like_clause('source')} OR {_like_clause('input_text')} OR {_like_clause('source_title')})",
                "source/input_text/source_title LIKE '%M12_DEMO%'",
            ),
            (
                "event_timeline",
                f"({_like_clause('timeline_json')} OR {_like_clause('error_message')})",
                "timeline_json/error_message LIKE '%M12_DEMO%'",
            ),
            (
                "browse_history",
                "target_type = 'post' AND target_id IN (SELECT id FROM community_post WHERE title LIKE '%M12_DEMO%')",
                "browse_history for M12_DEMO posts (indirect, safe)",
            ),
            (
                "favorite",
                "target_type = 'post' AND target_id IN (SELECT id FROM community_post WHERE title LIKE '%M12_DEMO%')",
                "favorite for M12_DEMO posts (indirect, safe)",
            ),
            (
                "admin_operation_log",
                f"({_like_clause('description')} OR {_like_clause('error_message')} OR {_like_clause('user_agent')})",
                "description/error_message/user_agent LIKE '%M12_DEMO%'",
            ),
            (
                "backup_record",
                _like_clause("backup_name"),
                "backup_name LIKE '%M12_DEMO%'",
            ),
        ]

        # ── Phase 1: Count ───────────────────────────────────────
        total = 0
        print("\n[Phase 1] Counting rows to delete...\n")
        counts: dict[str, int] = {}
        for table, where, label in rules:
            cnt = _count(db, table, where)
            counts[table] = cnt
            if cnt > 0:
                print(f"  {table}: {cnt} rows")
                total += cnt
            else:
                print(f"  {table}: 0 rows (skip)")

        print("\n  [TOTAL] rows to delete: " + str(total))

        if total == 0:
            print("\n[OK] No M12 demo data found. Nothing to clean.")
            return

        # ── Phase 2: Confirm ─────────────────────────────────────
        print("\n" + "─" * 60)
        print("[WARNING] ABOUT TO DELETE THE ABOVE ROWS.")
        print("   This only affects rows containing M12_DEMO / M12_TEST.")
        print("   Real business data is NOT affected.")
        print("   admin / editor / user accounts are NOT modified.")
        print("─" * 60)

        if "--yes" not in sys.argv:
            answer = input("\nProceed? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                print("[ABORTED] Aborted by user.")
                return

        # ── Phase 3: Delete ──────────────────────────────────────
        print("\n[Phase 2] Deleting...\n")
        deleted_total = 0
        for table, where, _label in rules:
            if counts.get(table, 0) == 0:
                continue
            n = _delete(db, table, where)
            db.commit()
            print("  " + table + ": deleted " + str(n) + " rows [OK]")
            deleted_total += n

        print("\n  [TOTAL] deleted: " + str(deleted_total))
        print("\n[OK] Cleanup complete.")

    except Exception as exc:
        db.rollback()
        print("[ERROR] " + str(exc), file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
