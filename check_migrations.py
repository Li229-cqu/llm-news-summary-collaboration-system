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
    ('001 source_url', "COLUMNS", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='news' AND COLUMN_NAME='source_url'"),
    ('005 user_category_subscription', "TABLES", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='user_category_subscription'"),
    ('006 ft_news_search index', "STATISTICS", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='news' AND INDEX_NAME='ft_news_search'"),
    ('007 editor column', "COLUMNS", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='news' AND COLUMN_NAME='editor'"),
    ('008 hot_topic_status', "COLUMNS", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='hot_topic' AND COLUMN_NAME='status'"),
    ('010 post_comment_media', "COLUMNS", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='post_comment' AND COLUMN_NAME='media_json'"),
    ('011 news_comment_media', "COLUMNS", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='news_comment' AND COLUMN_NAME='media_json'"),
    ('012 ai_source', "COLUMNS", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='ai_generate_record' AND COLUMN_NAME='ai_source'"),
    ('013 view_count', "COLUMNS", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='community_post' AND COLUMN_NAME='view_count'"),
    ('014 browse_history_target_type', "COLUMNS", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='browse_history' AND COLUMN_NAME='target_type'"),
    ('017 profile_weekly_report_cache', "TABLES", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='profile_weekly_report_cache'"),
    ('018 system_config', "TABLES", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='system_config'"),
    ('019 ai_prompt_template', "TABLES", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='ai_prompt_template'"),
    ('020 admin_operation_log', "TABLES", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='admin_operation_log'"),
    ('021 backup_record', "TABLES", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='backup_record'"),
    ('022 community_ai_session', "TABLES", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='community_ai_session'"),
    ('022 community_ai_message', "TABLES", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='community_ai_message'"),
    ('023 detail_fields', "COLUMNS", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='profile_weekly_report_cache' AND COLUMN_NAME='page_analyses_overview'"),
    ('025 event table', "TABLES", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='event'"),
    ('027 response_ms', "COLUMNS", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='ai_generate_record' AND COLUMN_NAME='response_ms'"),
    ('028 post_images', "COLUMNS", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='community_post' AND COLUMN_NAME='images'"),
    ('029 agent_task', "TABLES", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='agent_task'"),
    ('029 agent_step_log', "TABLES", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='agent_step_log'"),
    ('029 source_type', "COLUMNS", f"TABLE_SCHEMA='{DB}' AND TABLE_NAME='news_topic' AND COLUMN_NAME='source_type'"),
]
print('=== Migration Status ===')
all_pass = True
for name, obj_type, where in checks:
    sql = f"SELECT count(1) FROM information_schema.{obj_type} WHERE {where}"
    cur.execute(sql)
    cnt = cur.fetchone()[0]
    mark = 'PASS' if cnt > 0 else 'MISS'
    if cnt == 0:
        all_pass = False
    print(f'  [{mark}] {name}')

if all_pass:
    print('\nAll migrations have been applied.')
else:
    print('\nSome migrations are missing.')

# List all tables
cur.execute(f"SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='{DB}' ORDER BY TABLE_NAME")
tables = [r[0] for r in cur.fetchall()]
print(f'\n=== All tables ({len(tables)}) ===')
for t in tables:
    print(f'  {t}')

cur.close()
conn.close()
