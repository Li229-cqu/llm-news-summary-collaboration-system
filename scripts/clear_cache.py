import pymysql
c=pymysql.connect(host='127.0.0.1',port=3306,user='llm_news_user',password='123456',database='llm_news_system',charset='utf8mb4',autocommit=True).cursor()
c.execute("DELETE FROM profile_weekly_report_cache WHERE user_id=5 AND report_date=CURDATE()")
print(f'Deleted {c.rowcount} rows')
c.execute("SELECT COUNT(*) FROM profile_weekly_report_cache WHERE user_id=5")
print(f'Remaining: {c.fetchone()[0]} rows')
c.close()
