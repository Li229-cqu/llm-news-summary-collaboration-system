import pymysql, time
c = pymysql.connect(host='127.0.0.1',port=3306,user='llm_news_user',
    password='123456',database='llm_news_system',charset='utf8mb4').cursor()

print("=== 各表数据量 ===")
for t in ['browse_history','favorite','user_like','news_comment','post_comment',
          'community_post','news','ai_generate_record','profile_weekly_report_cache']:
    c.execute(f'SELECT COUNT(*) FROM {t}')
    print(f'  {t:35s}: {c.fetchone()[0]:6d}')

print("\n=== browse_history 索引 ===")
c.execute('SHOW INDEX FROM browse_history')
for r in c.fetchall():
    print(f'  {r[2]:30s} {r[4]}')

print("\n=== EXPLAIN: 近7天浏览用户5 ===")
c.execute("EXPLAIN SELECT COUNT(*) FROM browse_history WHERE user_id=5 AND browse_time>='2026-06-27'")
for r in c.fetchall(): print(f'  {r}')

print("\n=== EXPLAIN: 全部浏览历史用户5 ===")
c.execute("EXPLAIN SELECT COUNT(*) FROM browse_history WHERE user_id=5")
for r in c.fetchall(): print(f'  {r}')

print("\n=== EXPLAIN: favorite 用户5 ===")
c.execute("EXPLAIN SELECT * FROM favorite WHERE user_id=5")
for r in c.fetchall(): print(f'  {r}')

print("\n=== EXPLAIN: news_comment 用户5 ===")
c.execute("EXPLAIN SELECT * FROM news_comment WHERE user_id=5")
for r in c.fetchall(): print(f'  {r}')

# 检查 profile_weekly_report_cache 表大小
c.execute("SELECT user_id, range_days, report_date, CHAR_LENGTH(ai_summary) as sum_len, CHAR_LENGTH(ai_insights) as ins_len, CHAR_LENGTH(ai_suggestions) as sug_len, CHAR_LENGTH(page_analyses_overview) as ov_len FROM profile_weekly_report_cache")
print("\n=== profile_weekly_report_cache 内容大小 ===")
for r in c.fetchall():
    total = sum(x or 0 for x in r[3:])
    print(f'  user={r[0]} days={r[1]} date={r[2]} total_bytes={total}')

c.close()
print("\nDone")
