"""M7.5 hot-topic & topic management integration test script — v2."""
import requests
import json

BASE = "http://127.0.0.1:8000/api"

tokens = {
    "admin": "mock-token-admin",
    "editor": "mock-token-editor",
    "user": "mock-token-user",
}

def api(method, path, token=None, json_data=None, params=None):
    url = f"{BASE}{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if json_data is not None:
        headers["Content-Type"] = "application/json"
        r = requests.request(method, url, headers=headers, json=json_data)
    else:
        r = requests.request(method, url, headers=headers, params=params)
    try:
        return r.status_code, r.json()
    except:
        return r.status_code, {"raw": r.text[:300]}

def log(msg):
    print(f"  {msg}")

def test(name, status_code, resp, expected_code=None):
    ok = True
    if expected_code is not None and status_code != expected_code:
        ok = False
        print(f"  FAIL: {name} - expected HTTP {expected_code}, got {status_code}")
        print(f"        resp: {json.dumps(resp, ensure_ascii=False)[:300]}")
    elif status_code >= 500:
        ok = False
        print(f"  FAIL: {name} - HTTP {status_code} (server error)")
        print(f"        resp: {json.dumps(resp, ensure_ascii=False)[:300]}")
    elif status_code >= 400 and expected_code is None:
        print(f"  WARN: {name} - HTTP {status_code}")
        print(f"        resp: {json.dumps(resp, ensure_ascii=False)[:300]}")
    else:
        print(f"  PASS: {name} - HTTP {status_code}")
    return ok

# ================================================
# Task 2: Create M7_TEST data
# ================================================
print("=== Task 2: Create M7_TEST data ===\n")

# 2.1 Create test topic
print("2.1 Creating M7_TEST topic via API:")
code, resp = api("POST", "/admin/topics", token=tokens["admin"], json_data={
    "topic_name": "M7_TEST 话题",
    "summary": "M7.5 热搜与话题管理联调用测试话题",
    "keyword_list": "M7_TEST,后台联调,话题测试",
    "heat_score": 50,
    "status": 1
})
test("Create M7_TEST topic", code, resp)
topic_id = None
if code == 200 and resp.get("data"):
    topic_id = resp["data"].get("topic_id")
    print(f"  Topic ID: {topic_id}")
else:
    # Fallback: find existing
    code2, resp2 = api("GET", "/admin/topics", token=tokens["admin"], params={"keyword": "M7_TEST", "page": 1, "page_size": 10})
    if code2 == 200 and resp2.get("data") and resp2["data"].get("items"):
        topic_id = resp2["data"]["items"][0]["id"]
        print(f"  Topic already exists, using ID: {topic_id}")
    else:
        print(f"  ERROR: no topic available")
        topic_id = None

# 2.2 Find existing M7_TEST news or create one via DB
print("\n2.2 Checking for M7_TEST news:")
import pymysql
conn = pymysql.connect(host='127.0.0.1', port=3306, user='llm_news_user', password='123456', database='llm_news_system')
cur = conn.cursor()

# Find any 2 existing news articles we can use as test data
cur.execute("SELECT id, title, topic_id FROM news WHERE status=1 ORDER BY id DESC LIMIT 5")
existing_news = cur.fetchall()
m7_news_ids = []
original_topic_ids = {}

# Also check if we already have M7_TEST news
cur.execute("SELECT id, title, topic_id FROM news WHERE title LIKE '%M7_TEST%'")
m7_news = cur.fetchall()
if m7_news:
    m7_news_ids = [r[0] for r in m7_news]
    original_topic_ids.update({r[0]: r[2] for r in m7_news})
    print(f"  Found existing M7_TEST news: {m7_news_ids}")
else:
    # Insert 2 test news via SQL
    print(f"  Creating M7_TEST news via SQL...")
    cur.execute("INSERT INTO news (title, summary, content, source, publish_time, status, topic_id, created_at, updated_at) VALUES (%s, %s, %s, %s, NOW(), 1, NULL, NOW(), NOW())",
        ("M7_TEST 新闻 1", "M7.5测试新闻摘要1", "M7.5 测试新闻内容", "M7_TEST_SOURCE"))
    nid1 = cur.lastrowid
    cur.execute("INSERT INTO news (title, summary, content, source, publish_time, status, topic_id, created_at, updated_at) VALUES (%s, %s, %s, %s, NOW(), 1, NULL, NOW(), NOW())",
        ("M7_TEST 新闻 2", "M7.5测试新闻摘要2", "M7.5 测试新闻内容2", "M7_TEST_SOURCE"))
    nid2 = cur.lastrowid
    conn.commit()
    m7_news_ids = [nid1, nid2]
    original_topic_ids = {nid1: None, nid2: None}
    print(f"  Created M7_TEST news: {m7_news_ids}")

# 2.3 Create test hot topic
print("\n2.3 Creating M7_TEST hot_topic:")
cur.execute("SELECT id FROM hot_topic WHERE title LIKE '%M7_TEST%'")
existing_hot = cur.fetchone()
if existing_hot:
    hot_id = existing_hot[0]
    print(f"  Found existing M7_TEST hot_topic: id={hot_id}")
else:
    target_type = "topic" if topic_id else "news"
    target_id = topic_id if topic_id else (m7_news_ids[0] if m7_news_ids else None)
    if target_id:
        cur.execute("""
            INSERT INTO hot_topic (title, target_type, target_id, heat_score, rank_no, tag, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (f"M7_TEST 热搜", target_type, target_id, 100, 99, "M7_TEST", 1))
        conn.commit()
        hot_id = cur.lastrowid
        print(f"  Created M7_TEST hot_topic: id={hot_id}, target_type={target_type}, target_id={target_id}")
    else:
        print(f"  WARNING: No valid target_id for hot_topic")
        hot_id = None

cur.close()
conn.close()

print(f"\nM7_TEST IDs: topic_id={topic_id}, news_ids={m7_news_ids}, hot_id={hot_id}")

# ================================================
# Task 3: Hot Topics API Testing
# ================================================
print("\n\n=== Task 3: Hot Topics API Testing ===\n")

if hot_id:
    # 3.1 Hot topic list
    print("3.1 Hot topic list:")
    code, resp = api("GET", "/admin/hot-topics", token=tokens["admin"], params={"keyword": "M7_TEST", "page": 1, "page_size": 10})
    test("Hot topic list", code, resp)
    if code == 200:
        data = resp.get("data", {})
        print(f"  items count: {len(data.get('items', []))}")
        print(f"  total: {data.get('total')}")
        support = data.get('support', {})
        print(f"  support.pin_supported: {support.get('pin_supported')}")
        print(f"  support.hide_supported: {support.get('hide_supported')}")
        print(f"  support.hide_uses_status: {support.get('hide_uses_status')}")
        print(f"  support.manual_rank_supported: {support.get('manual_rank_supported')}")

    # 3.2 Hot topic detail
    print("\n3.2 Hot topic detail:")
    code, resp = api("GET", f"/admin/hot-topics/{hot_id}", token=tokens["admin"])
    test("Hot topic detail", code, resp)
    if code == 200:
        data = resp.get("data", {})
        print(f"  title: {data.get('title')}")
        print(f"  target_type: {data.get('target_type')}, target_id: {data.get('target_id')}")
        print(f"  target_missing: {data.get('target_missing')}")
        related = data.get('related_target', {})
        print(f"  related_target: type={related.get('type')}, title={related.get('title')}, missing={related.get('missing')}")

    # 3.3 Update rank
    print("\n3.3 Update rank:")
    code, resp = api("POST", f"/admin/hot-topics/{hot_id}/rank", token=tokens["admin"], json_data={"rank_no": 1})
    test("Update rank", code, resp)
    if code == 200:
        data = resp.get("data", {})
        print(f"  action={data.get('action')}, rank_no={data.get('rank_no')}")

    # 3.4 Hide
    print("\n3.4 Hide hot topic:")
    code, resp = api("POST", f"/admin/hot-topics/{hot_id}/hide", token=tokens["admin"])
    test("Hide hot topic", code, resp)
    if code == 200:
        data = resp.get("data", {})
        print(f"  action={data.get('action')}, status={data.get('status')}")

    # 3.5 Restore (using DELETE)
    print("\n3.5 Restore hot topic (DELETE /hide):")
    code, resp = api("DELETE", f"/admin/hot-topics/{hot_id}/hide", token=tokens["admin"])
    test("Restore hot topic", code, resp)
    if code == 200:
        data = resp.get("data", {})
        print(f"  action={data.get('action')}, status={data.get('status')}")

    # Verify DB
    print("\n3.6 Verify DB state:")
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='llm_news_user', password='123456', database='llm_news_system')
    cur = conn.cursor()
    cur.execute("SELECT id, title, rank_no, status, updated_at FROM hot_topic WHERE id=%s", (hot_id,))
    row = cur.fetchone()
    print(f"  id={row[0]}, title={row[1]}, rank_no={row[2]}, status={row[3]}, updated_at={row[4]}")
    cur.close()
    conn.close()
else:
    print("SKIPPING Task 3 - no hot_id")

# 3.7 Pin (expected 400)
print("\n3.7 Pin test (expected 400):")
one_id = hot_id or 1
code, resp = api("POST", f"/admin/hot-topics/{one_id}/pin", token=tokens["admin"])
test("POST pin returns 400", code, resp, expected_code=400)
if code == 400:
    print(f"  message: {resp.get('message', resp.get('detail', ''))}")

code2, resp2 = api("DELETE", f"/admin/hot-topics/{one_id}/pin", token=tokens["admin"])
test("DELETE pin returns 400", code2, resp2, expected_code=400)
if code2 == 400:
    print(f"  message: {resp2.get('message', resp2.get('detail', ''))}")

# ================================================
# Task 4: Topic Management API Testing
# ================================================
print("\n\n=== Task 4: Topic Management API Testing ===\n")

if topic_id:
    # 4.1 Topic list
    print("4.1 Topic list:")
    code, resp = api("GET", "/admin/topics", token=tokens["admin"], params={"keyword": "M7_TEST", "page": 1, "page_size": 10})
    test("Topic list", code, resp)
    if code == 200:
        data = resp.get("data", {})
        print(f"  items count: {len(data.get('items', []))}, total: {data.get('total')}")
        print(f"  summary: {data.get('summary')}")

    # 4.2 Topic detail
    print("\n4.2 Topic detail:")
    code, resp = api("GET", f"/admin/topics/{topic_id}", token=tokens["admin"])
    test("Topic detail", code, resp)
    if code == 200:
        data = resp.get("data", {})
        print(f"  topic_name: {data.get('topic_name')}")
        print(f"  keyword_list: {data.get('keyword_list')}")
        print(f"  status: {data.get('status')}, news_count: {data.get('news_count')}")

    # 4.3 Edit topic
    print("\n4.3 Edit topic:")
    code, resp = api("PUT", f"/admin/topics/{topic_id}", token=tokens["admin"], json_data={
        "topic_name": "M7_TEST 话题_已编辑",
        "summary": "M7.5 编辑测试",
        "keyword_list": "M7_TEST,编辑测试,后台联调",
        "status": 1
    })
    test("Edit topic", code, resp)
    if code == 200:
        data = resp.get("data", {})
        print(f"  action={data.get('action')}, status={data.get('status')}, message={data.get('message')}")

    # 4.4 Disable topic
    print("\n4.4 Disable topic:")
    code, resp = api("POST", f"/admin/topics/{topic_id}/status", token=tokens["admin"], json_data={"status": 0})
    test("Disable topic", code, resp)
    if code == 200:
        data = resp.get("data", {})
        print(f"  action={data.get('action')}, status={data.get('status')}")

    # 4.5 Enable topic
    print("\n4.5 Enable topic:")
    code, resp = api("POST", f"/admin/topics/{topic_id}/status", token=tokens["admin"], json_data={"status": 1})
    test("Enable topic", code, resp)
    if code == 200:
        data = resp.get("data", {})
        print(f"  action={data.get('action')}, status={data.get('status')}")

    # Verify DB
    print("\n4.6 Verify DB state:")
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='llm_news_user', password='123456', database='llm_news_system')
    cur = conn.cursor()
    cur.execute("SELECT id, topic_name, summary, keyword_list, status, updated_at FROM news_topic WHERE id=%s", (topic_id,))
    row = cur.fetchone()
    print(f"  id={row[0]}, topic_name={row[1]}, summary={row[2]}, keyword_list={row[3]}, status={row[4]}, updated_at={row[5]}")
    cur.close()
    conn.close()
else:
    print("SKIPPING Task 4 - no topic_id")

# ================================================
# Task 5: Topic-News Association Testing
# ================================================
print("\n\n=== Task 5: Topic-News Association Testing ===\n")

if topic_id and m7_news_ids:
    # 5.1 Candidate news
    print("5.1 Candidate news:")
    code, resp = api("GET", f"/admin/topics/{topic_id}/candidate-news", token=tokens["admin"], params={"keyword": "M7_TEST", "page": 1, "page_size": 10})
    test("Candidate news", code, resp)
    if code == 200:
        data = resp.get("data", {})
        print(f"  items count: {len(data.get('items', []))}, total: {data.get('total')}")

    # 5.2 Bind news
    print("\n5.2 Bind news to topic:")
    code, resp = api("POST", f"/admin/topics/{topic_id}/bind-news", token=tokens["admin"], json_data={"news_ids": m7_news_ids})
    test("Bind news", code, resp)
    if code == 200:
        data = resp.get("data", {})
        print(f"  action={data.get('action')}, affected_count={data.get('affected_count')}")

    # 5.3 View bound news
    print("\n5.3 View topic's bound news:")
    code, resp = api("GET", f"/admin/topics/{topic_id}/news", token=tokens["admin"], params={"page": 1, "page_size": 10})
    test("Topic's bound news", code, resp)
    if code == 200:
        data = resp.get("data", {})
        items = data.get('items', [])
        print(f"  items count: {len(items)}, total: {data.get('total')}")
        for item in items[:3]:
            print(f"  - id={item.get('id')}, title={item.get('title')}, topic_id={item.get('topic_id')}")

    # 5.4 Verify DB
    print("\n5.4 Verify DB after bind:")
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='llm_news_user', password='123456', database='llm_news_system')
    cur = conn.cursor()
    for nid in m7_news_ids:
        cur.execute("SELECT id, title, topic_id FROM news WHERE id=%s", (nid,))
        row = cur.fetchone()
        ok_str = "OK" if row and row[2] == topic_id else f"FAIL: expected {topic_id}, got {row[2] if row else 'N/A'}"
        print(f"  news id={nid}: topic_id={row[2] if row else 'N/A'} ({ok_str})")
    cur.close()
    conn.close()

    # 5.5 Unbind news
    print("\n5.5 Unbind news from topic:")
    code, resp = api("POST", f"/admin/topics/{topic_id}/unbind-news", token=tokens["admin"], json_data={"news_ids": m7_news_ids})
    test("Unbind news", code, resp)
    if code == 200:
        data = resp.get("data", {})
        print(f"  action={data.get('action')}, affected_count={data.get('affected_count')}")

    # 5.6 Verify DB after unbind
    print("\n5.6 Verify DB after unbind:")
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='llm_news_user', password='123456', database='llm_news_system')
    cur = conn.cursor()
    for nid in m7_news_ids:
        cur.execute("SELECT id, title, topic_id FROM news WHERE id=%s", (nid,))
        row = cur.fetchone()
        ok_str = "OK (cleared)" if row and row[2] is None else f"FAIL: expected NULL, got {row[2] if row else 'N/A'}"
        print(f"  news id={nid}: topic_id={row[2] if row else 'N/A'} ({ok_str})")
    cur.close()
    conn.close()

else:
    print("SKIPPING Task 5 - no topic_id or no news_ids")

# ================================================
# Task 6: Permission Testing
# ================================================
print("\n\n=== Task 6: Permission Testing ===\n")

print("6.1 Admin:")
code, resp = api("GET", "/admin/hot-topics", token=tokens["admin"])
test("Admin GET /hot-topics", code, resp)
code, resp = api("GET", "/admin/topics", token=tokens["admin"])
test("Admin GET /topics", code, resp)

print("\n6.2 Editor:")
code, resp = api("GET", "/admin/hot-topics", token=tokens["editor"])
test("Editor GET /hot-topics", code, resp)
code, resp = api("GET", "/admin/topics", token=tokens["editor"])
test("Editor GET /topics", code, resp)

print("\n6.3 User (expect 403):")
code, resp = api("GET", "/admin/hot-topics", token=tokens["user"])
test("User GET /hot-topics -> 403", code, resp, expected_code=403)
code, resp = api("GET", "/admin/topics", token=tokens["user"])
test("User GET /topics -> 403", code, resp, expected_code=403)

print("\n6.4 Unauthenticated (expect 401):")
code, resp = api("GET", "/admin/hot-topics")
test("No token GET /hot-topics -> 401", code, resp, expected_code=401)
code, resp = api("GET", "/admin/topics")
test("No token GET /topics -> 401", code, resp, expected_code=401)

# ================================================
# Task 9: Clean up M7_TEST data
# ================================================
print("\n\n=== Task 9: Clean up M7_TEST data ===\n")

conn = pymysql.connect(host='127.0.0.1', port=3306, user='llm_news_user', password='123456', database='llm_news_system')
cur = conn.cursor()

print("Before cleanup:")
cur.execute("SELECT id, title FROM hot_topic WHERE title LIKE '%M7_TEST%'")
hot_before = cur.fetchall()
print(f"  hot_topic: {len(hot_before)} items - {[(r[0], r[1]) for r in hot_before]}")

cur.execute("SELECT id, topic_name FROM news_topic WHERE topic_name LIKE '%M7_TEST%'")
topics_before = cur.fetchall()
print(f"  news_topic: {len(topics_before)} items - {[(r[0], r[1]) for r in topics_before]}")

cur.execute("SELECT id, title, topic_id FROM news WHERE title LIKE '%M7_TEST%'")
news_before = cur.fetchall()
print(f"  news: {len(news_before)} items - {[(r[0], r[1], r[2]) for r in news_before]}")

# Delete M7_TEST hot_topics
for row in hot_before:
    cur.execute("DELETE FROM hot_topic WHERE id=%s", (row[0],))
    print(f"  Deleted hot_topic id={row[0]}")

# Unbind and delete M7_TEST news_topics
for row in topics_before:
    cur.execute("UPDATE news SET topic_id=NULL WHERE topic_id=%s", (row[0],))
    cur.execute("DELETE FROM news_topic WHERE id=%s", (row[0],))
    print(f"  Unbound news + deleted news_topic id={row[0]}")

# Restore original topic_ids for pre-existing news, delete M7_TEST-only news
for row in news_before:
    nid, title, tid = row
    orig = original_topic_ids.get(nid)
    if orig is not None:
        cur.execute("UPDATE news SET topic_id=%s WHERE id=%s", (orig, nid))
        print(f"  Restored news id={nid} topic_id to {orig}")
    else:
        # This was a newly created M7_TEST news — delete it
        cur.execute("DELETE FROM news WHERE id=%s", (nid,))
        print(f"  Deleted news id={nid}")

conn.commit()

# Verify
print("\nAfter cleanup:")
cur.execute("SELECT id, title FROM hot_topic WHERE title LIKE '%M7_TEST%'")
hot_after = cur.fetchall()
print(f"  hot_topic remaining: {len(hot_after)}")
cur.execute("SELECT id, topic_name FROM news_topic WHERE topic_name LIKE '%M7_TEST%'")
topics_after = cur.fetchall()
print(f"  news_topic remaining: {len(topics_after)}")
cur.execute("SELECT id, title, topic_id FROM news WHERE title LIKE '%M7_TEST%'")
news_after = cur.fetchall()
print(f"  news remaining: {len(news_after)}")

cur.close()
conn.close()

print("\n\n=== M7.5 TEST COMPLETE ===")
