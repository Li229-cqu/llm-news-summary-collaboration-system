import pymysql, os

conn = pymysql.connect(
    host=os.environ['DB_HOST'],
    port=int(os.environ['DB_PORT']),
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    database=os.environ['DB_NAME'],
    charset='utf8mb4'
)
cur = conn.cursor()
DB = os.environ['DB_NAME']

checks = [
    ('006 ft_news_search index', f"SELECT count(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA='{DB}' AND TABLE_NAME='news' AND INDEX_NAME='ft_news_search'"),
    ('007 editor column (not editor_id)', f"SELECT count(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='{DB}' AND TABLE_NAME='news' AND COLUMN_NAME='editor'"),
    ('017 weekly_report table', f"SELECT count(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='{DB}' AND TABLE_NAME='profile_weekly_report_cache'"),
    ('022 community_ai_session table', f"SELECT count(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='{DB}' AND TABLE_NAME='community_ai_session'"),
    ('022 community_ai_message table', f"SELECT count(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='{DB}' AND TABLE_NAME='community_ai_message'"),
    ('023 detail fields (page_analyses_overview)', f"SELECT count(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='{DB}' AND TABLE_NAME='profile_weekly_report_cache' AND COLUMN_NAME='page_analyses_overview'"),
    ('023 detail fields (closing)', f"SELECT count(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='{DB}' AND TABLE_NAME='profile_weekly_report_cache' AND COLUMN_NAME='closing'"),
]
print('=== Corrected Recheck ===')
for name, sql in checks:
    cur.execute(sql)
    cnt = cur.fetchone()[0]
    mark = 'PASS' if cnt > 0 else 'MISS'
    print(f'  [{mark}] {name}')

# List all tables
cur.execute(f"SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='{DB}' ORDER BY TABLE_NAME")
tables = [r[0] for r in cur.fetchall()]
print(f'\n=== Tables in database ({len(tables)}) ===')
for t in tables:
    print(f'  {t}')

cur.close()
conn.close()
