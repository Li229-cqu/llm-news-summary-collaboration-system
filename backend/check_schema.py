"""Check DB event_timeline schema + data."""
import pymysql
conn = pymysql.connect(host='127.0.0.1', port=3306, user='llm_news_user', password='123456', database='llm_news_system', charset='utf8mb4')
cur = conn.cursor()

print("=== event_timeline schema ===")
cur.execute("DESC event_timeline")
for r in cur.fetchall():
    print(f"  {r[0]:20s} {r[1]:20s} {r[2]:8s} {r[3]:8s} {r[4]}")

print("\n=== news_topic schema ===")
cur.execute("DESC news_topic")
for r in cur.fetchall():
    print(f"  {r[0]:20s} {r[1]:20s} {r[2]:8s} {r[3]:8s} {r[4]}")

print("\n=== news schema ===")
cur.execute("DESC news")
for r in cur.fetchall():
    print(f"  {r[0]:20s} {r[1]:20s} {r[2]:8s} {r[3]:8s} {r[4]}")

print("\n=== event_timeline data ===")
cur.execute("SELECT id, topic_id, generate_status, INSTR(timeline_json, 'event_id') as has_timeline, INSTR(source_news_ids, '[') as has_src, generated_at, updated_at FROM event_timeline")
for r in cur.fetchall():
    print(f"  id={r[0]}, topic_id={r[1]}, status={r[2]}, has_json={r[3]>0}, has_src={r[4]>0}, gen_at={r[5]}, upd_at={r[6]}")

print("\n=== topic+news counts ===")
cur.execute("SELECT nt.id, nt.topic_name, COUNT(n.id) as news_cnt FROM news_topic nt LEFT JOIN news n ON n.topic_id=nt.id GROUP BY nt.id")
for r in cur.fetchall():
    print(f"  topic id={r[0]}, name={r[1]:20s}, news_count={r[2]}")

cur.close()
conn.close()
