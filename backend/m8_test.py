"""
M8: Admin Timeline Management — Integration Test Script
Tests all 7 M8 endpoints against the running backend.
"""
import requests
import json
import time

BASE = "http://localhost:8000"

# ── Step 0: Login as admin ──────────────────────────────────────
print("=" * 60)
print("Step 0: Login as admin")

# Try common admin credentials
creds_tried = []
for pw in ["admin", "admin123456", "123456", "password"]:
    r = requests.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": pw})
    if r.status_code == 200:
        data = r.json()
        print(f"  ✓ Login success with password: {pw}")
        print(f"  User info: {json.dumps(data.get('data', {}).get('user', {}), ensure_ascii=False)}")
        creds_tried.append(("admin", pw, data))
        break
    else:
        creds_tried.append(("admin", pw, r.json()))

if not any(c[2] for c in creds_tried if isinstance(c[2], dict) and c[2].get('code') == 200):
    # Try to find the actual admin user
    print("  Could not login as admin. Trying to check DB...")
    print(f"  Attempts: {[(c[0], c[1], c[2] if isinstance(c[2], str) else c[2].get('message')) for c in creds_tried]}")
    exit(1)

token = creds_tried[-1][2]['data']['token']
admin_user = creds_tried[-1][2]['data']['user']
headers = {"Authorization": f"Bearer {token}"}
print(f"  Token: {token[:40]}...")
print(f"  Role: {admin_user.get('role')}")


# ── Step 1: GET /api/admin/timelines/options ────────────────────
print("\n" + "=" * 60)
print("M8-1: GET /api/admin/timelines/options")
r = requests.get(f"{BASE}/api/admin/timelines/options", headers=headers)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()['data']
    print(f"  status_options: {json.dumps(data.get('status_options', []), ensure_ascii=False)}")
    print(f"  news_count_options: {json.dumps(data.get('news_count_options', []), ensure_ascii=False)}")
    print(f"  support: {json.dumps(data.get('support', {}), ensure_ascii=False)}")
else:
    print(f"  Error: {r.json()}")


# ── Step 2: GET /api/admin/timelines ────────────────────────────
print("\n" + "=" * 60)
print("M8-2: GET /api/admin/timelines")
r = requests.get(f"{BASE}/api/admin/timelines", headers=headers)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()['data']
    print(f"  total: {data.get('total')}")
    print(f"  summary: {json.dumps(data.get('summary', {}), ensure_ascii=False)}")
    items = data.get('items', [])
    print(f"  items count: {len(items)}")
    for i, item in enumerate(items[:5]):
        print(f"  [{i}] id={item.get('topic_id')} name={item.get('topic_name')} status={item.get('generate_status')} cache={item.get('cache_status')} news={item.get('news_count')}")
else:
    print(f"  Error: {r.json()}")


# ── Step 3: Pick a topic and test detail endpoint ────────────────
print("\n" + "=" * 60)
print("M8-3: GET /api/admin/timelines/{topic_id}")
items = data.get('items', [])
if not items:
    print("  WARNING: No topics found. M8 endpoints need news_topic records.")
    print("  Creating test topic and news via M7 API...")

    # Create topic through admin API
    topic_payload = {
        "topic_name": "M8_TEST_测试话题",
        "keyword_list": "M8测试,集成测试,timeline",
        "description": "M8 integration test topic",
        "type": "normal",
        "status": 1
    }
    r = requests.post(f"{BASE}/api/admin/topics", json=topic_payload, headers=headers)
    print(f"  Create topic status: {r.status_code}, response: {json.dumps(r.json(), ensure_ascii=False)[:300]}")
    if r.status_code == 200 and r.json().get('data'):
        topic_id = r.json()['data'].get('topic_id') or r.json()['data'].get('id')
    else:
        # try existing topics via hot-topic list
        r = requests.get(f"{BASE}/api/admin/hot-topics", headers=headers)
        print(f"  Hot topic list status: {r.status_code}")
        if r.status_code == 200 and r.json().get('data', {}).get('items'):
            topic_id = r.json()['data']['items'][0]['id']
            print(f"  Using existing hot topic: {topic_id}")
        else:
            print("  ERROR: Cannot find or create any topic. Aborting M8 tests.")
            print(f"  Hot topic response: {json.dumps(r.json(), ensure_ascii=False)[:500]}")
            exit(1)

    print(f"  topic_id: {topic_id}")
else:
    topic_id = items[0]['topic_id']
    print(f"  Using existing topic: {topic_id} ({items[0]['topic_name']})")

# Test detail
r = requests.get(f"{BASE}/api/admin/timelines/{topic_id}", headers=headers)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    detail = r.json()['data']
    print(f"  topic_name: {detail.get('topic_name')}")
    print(f"  generate_status: {detail.get('generate_status')}")
    print(f"  source_news_ids: {detail.get('source_news_ids')}")
    print(f"  timeline_nodes count: {len(detail.get('timeline_nodes', []))}")
    print(f"  source_news count: {len(detail.get('source_news', []))}")
    print(f"  cache_check: {json.dumps(detail.get('cache_check', {}), ensure_ascii=False)}")
else:
    print(f"  Error: {r.json()}")


# ── Step 4: GET /api/admin/timelines/{topic_id}/source-news ─────
print("\n" + "=" * 60)
print("M8-4: GET /api/admin/timelines/{topic_id}/source-news")
r = requests.get(f"{BASE}/api/admin/timelines/{topic_id}/source-news", headers=headers)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    sn_data = r.json()['data']
    print(f"  total: {sn_data.get('total')}")
    for i, item in enumerate(sn_data.get('items', [])[:5]):
        print(f"  [{i}] id={item.get('id')} title={item.get('title', '')[:50]} in_cache={item.get('in_source_news_ids')}")
else:
    print(f"  Error: {r.json()}")


# ── Step 5: POST /api/admin/timelines/{topic_id}/generate ──────
print("\n" + "=" * 60)
print("M8-5: POST /api/admin/timelines/{topic_id}/generate")
r = requests.post(f"{BASE}/api/admin/timelines/{topic_id}/generate", headers=headers)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    result = r.json()['data']
    print(f"  message: {result.get('message')}")
    print(f"  success: {result.get('success')}")
    print(f"  topic_id: {result.get('topic_id')}")
else:
    print(f"  Error: {r.json()}")


# ── Step 6: Re-check detail after generate ──────────────────────
print("\n" + "=" * 60)
print("M8-6: Verify timeline detail after generate")
r = requests.get(f"{BASE}/api/admin/timelines/{topic_id}", headers=headers)
if r.status_code == 200:
    detail2 = r.json()['data']
    print(f"  generate_status: {detail2.get('generate_status')}")
    print(f"  source_news_ids count: {len(detail2.get('source_news_ids', []))}")
    print(f"  timeline_nodes count: {len(detail2.get('timeline_nodes', []))}")
    if detail2.get('timeline_nodes'):
        node = detail2['timeline_nodes'][0]
        print(f"  First node: event_title={node.get('event_title')}, event_time={node.get('event_time')}")
    print(f"  cache_check: {json.dumps(detail2.get('cache_check', {}), ensure_ascii=False)}")
else:
    print(f"  Error: {r.json()}")


# ── Step 7: POST /api/admin/timelines/{topic_id}/refresh ───────
print("\n" + "=" * 60)
print("M8-7: POST /api/admin/timelines/{topic_id}/refresh")
r = requests.post(f"{BASE}/api/admin/timelines/{topic_id}/refresh", headers=headers)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    result = r.json()['data']
    print(f"  message: {result.get('message')}")
    print(f"  success: {result.get('success')}")
else:
    print(f"  Error: {r.json()}")


# ── Step 8: DELETE /api/admin/timelines/{topic_id}/cache ───────
print("\n" + "=" * 60)
print("M8-8: DELETE /api/admin/timelines/{topic_id}/cache")
r = requests.delete(f"{BASE}/api/admin/timelines/{topic_id}/cache", headers=headers)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    result = r.json()['data']
    print(f"  message: {result.get('message')}")
    print(f"  success: {result.get('success')}")
else:
    print(f"  Error: {r.json()}")

# Verify cache is cleared
r = requests.get(f"{BASE}/api/admin/timelines/{topic_id}", headers=headers)
if r.status_code == 200:
    detail3 = r.json()['data']
    expected_no_cache = detail3.get('generate_status') in ('not_generated', 'failed')
    print(f"  After delete: generate_status={detail3.get('generate_status')}, cache_cleared={detail3.get('cache_status') == 'no_cache'}")

print("\n" + "=" * 60)
print("M8 Integration Tests Complete!")
