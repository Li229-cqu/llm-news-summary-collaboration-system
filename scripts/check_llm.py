import pymysql
c = pymysql.connect(host='127.0.0.1', port=3306, user='llm_news_user',
    password='123456', database='llm_news_system', charset='utf8mb4').cursor()
c.execute("SELECT COUNT(*) FROM system_config")
print(f"system_config total: {c.fetchone()[0]}")
c.execute("SELECT config_key, config_value FROM system_config WHERE config_key LIKE '%llm%' OR config_key LIKE '%real%'")
rows = c.fetchall()
for r in rows:
    print(f"  {r[0]:40s} = {r[1]}")
if not rows:
    print("  No matching rows found")
    c.execute("SELECT config_key, config_value FROM system_config LIMIT 5")
    for r in c.fetchall():
        print(f"  {r[0]:40s} = {r[1]}")
c.close()
