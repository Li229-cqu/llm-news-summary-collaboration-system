import pymysql
c = pymysql.connect(host='127.0.0.1', port=3306, user='llm_news_user',
    password='123456', database='llm_news_system', charset='utf8mb4', autocommit=True).cursor()
c.execute("UPDATE system_config SET config_value='true' WHERE config_key='ai.enable_real_llm'")
c.execute("SELECT config_key, config_value FROM system_config WHERE config_key='ai.enable_real_llm'")
row = c.fetchone(); print(f'{row[0]} = {row[1]}')
c.close()
print('Done')
