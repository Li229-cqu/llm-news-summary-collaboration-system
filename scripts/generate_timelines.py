#!/usr/bin/env python3
"""Batch generate event_timeline cache for topics with >=2 news.

Usage:
    python scripts/generate_timelines.py --dry-run
    python scripts/generate_timelines.py --run
    python scripts/generate_timelines.py --run --topic-ids 14,15,16
"""

import argparse
import os
import sys
import time

import pymysql
import requests

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "llm_news_user"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "llm_news_system"),
    "charset": "utf8mb4",
}

DEFAULT_BASE_URL = "http://localhost:8000"
POLL_INTERVAL = 2.0
TIMEOUT_SECONDS = 60


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def get_pending_topics(conn, topic_ids=None):
    cur = conn.cursor()
    cur.execute("""
        SELECT nt.id, nt.topic_name, nt.heat_score, COUNT(n.id),
               et.id AS tl_id, et.generate_status
        FROM news_topic nt
        LEFT JOIN news n ON n.topic_id = nt.id AND n.status = 1
        LEFT JOIN event_timeline et ON et.topic_id = nt.id
        WHERE nt.status = 1
        GROUP BY nt.id, nt.topic_name, nt.heat_score, et.id, et.generate_status
        HAVING COUNT(n.id) >= 2
        ORDER BY nt.heat_score DESC
    """)
    rows = cur.fetchall()
    topics = []
    for r in rows:
        tid, name, heat, ncount, tl_id, tl_status = r
        if topic_ids and tid not in topic_ids:
            continue
        if tl_id and tl_status == "generated":
            topics.append({"id": tid, "name": name, "heat": heat, "news_count": ncount, "status": "cached"})
        else:
            topics.append({"id": tid, "name": name, "heat": heat, "news_count": ncount, "status": "pending"})
    return topics


def generate_one(base_url, topic):
    tid = topic["id"]
    name = topic["name"]
    url = f"{base_url}/api/timeline/topics/{tid}/generate"
    start = time.time()
    try:
        resp = requests.post(url, timeout=30)
        elapsed = time.time() - start
        if resp.status_code != 200:
            return {**topic, "result": "error", "error": f"HTTP {resp.status_code}: {resp.text[:200]}", "elapsed": elapsed}
        data = resp.json().get("data", {})
        gs = data.get("generate_status", "unknown")
        if gs == "generating":
            for _ in range(int(TIMEOUT_SECONDS / POLL_INTERVAL)):
                time.sleep(POLL_INTERVAL)
                try:
                    r2 = requests.get(f"{base_url}/api/timeline/topics/{tid}", timeout=10)
                    if r2.status_code == 200:
                        d2 = r2.json().get("data", {})
                        gs2 = d2.get("generate_status", "unknown")
                        if gs2 != "generating":
                            elapsed = time.time() - start
                            if gs2 in ("generated", "cached", "mock"):
                                return {**topic, "result": "ok", "generate_status": gs2, "elapsed": elapsed}
                            return {**topic, "result": "error", "error": f"status={gs2}", "elapsed": elapsed}
                except Exception:
                    pass
            return {**topic, "result": "timeout", "error": "polling timeout", "elapsed": time.time() - start}
        if gs in ("generated", "cached", "mock"):
            return {**topic, "result": "ok", "generate_status": gs, "elapsed": elapsed}
        return {**topic, "result": "error", "error": f"unexpected status={gs}", "elapsed": elapsed}
    except requests.RequestException as exc:
        return {**topic, "result": "error", "error": str(exc)[:200], "elapsed": time.time() - start}


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Batch generate event_timeline")
    parser.add_argument("--dry-run", action="store_true", help="List pending topics only")
    parser.add_argument("--run", action="store_true", help="Execute generation")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--topic-ids", type=str, default=None)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    topic_ids = None
    if args.topic_ids:
        topic_ids = set(int(x.strip()) for x in args.topic_ids.split(","))

    conn = get_connection()
    topics = get_pending_topics(conn, topic_ids)
    conn.close()

    print(f"{'='*60}")
    print(f"  Event Timeline Generation")
    print(f"  Backend: {base_url}")
    print(f"{'='*60}\n")

    cached = [t for t in topics if t["status"] == "cached"]
    pending = [t for t in topics if t["status"] == "pending"]
    print(f"  Cached (skip): {len(cached)}")
    for t in cached:
        print(f"    [{t['id']}] {t['name']} ({t['news_count']} news)")
    print(f"\n  Pending: {len(pending)}")
    for t in pending:
        print(f"    [{t['id']}] {t['name']} ({t['news_count']} news)")
    print()

    if args.dry_run or not args.run:
        print("  Dry-run complete. Use --run to execute generation.")
        return

    if not pending:
        print("  All topics already cached. Nothing to do.")
        return

    print("-" * 60)
    resp = input(f"  [!] Generate for {len(pending)} topics? Type 'YES': ").strip()
    if resp != "YES":
        print("  Aborted.")
        return

    results = []
    for i, t in enumerate(pending):
        print(f"\n  [{i+1}/{len(pending)}] Topic {t['id']}: {t['name']} ...")
        r = generate_one(base_url, t)
        results.append(r)
        if r["result"] == "ok":
            print(f"    SUCCESS ({r.get('generate_status')}) in {r['elapsed']:.1f}s")
        elif r["result"] == "timeout":
            print(f"    TIMEOUT after {r['elapsed']:.1f}s")
        else:
            print(f"    FAILED: {r.get('error', 'unknown')}")
        if i < len(pending) - 1:
            time.sleep(1)

    ok = [r for r in results if r["result"] == "ok"]
    fail = [r for r in results if r["result"] != "ok"]
    print(f"\n{'='*60}")
    print(f"  Done. Success: {len(ok)}, Failed: {len(fail)}")
    if fail:
        for r in fail:
            print(f"    [{r['id']}] {r['name']}: {r.get('error')}")
    print()


if __name__ == "__main__":
    main()
