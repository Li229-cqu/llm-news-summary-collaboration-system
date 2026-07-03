import pymysql
c = pymysql.connect(host='127.0.0.1', port=3306, user='llm_news_user',
    password='123456', database='llm_news_system', charset='utf8mb4').cursor()

tables = [('news','新闻'), ('user','用户'), ('community_post','社区帖子'),
    ('news_comment','新闻评论'), ('post_comment','帖子评论'),
    ('browse_history','浏览记录'), ('favorite','收藏'), ('user_like','点赞'),
    ('ai_generate_record','AI生成记录'), ('event_timeline','事件脉络'),
    ('community_ai_session','AI会话'), ('community_ai_message','AI消息'),
    ('profile_weekly_report_cache','周报缓存')]

print('=== 最终数据汇总 ===')
for t, name in tables:
    try:
        c.execute(f'SELECT COUNT(*) FROM `{t}`')
        print(f'  {name:12s}: {c.fetchone()[0]:5d}')
    except: pass

print('\n=== 普通用户互动统计 ===')
c.execute("SELECT id, nickname FROM user WHERE role='user' ORDER BY id")
for uid, nick in c.fetchall():
    stats = {}
    for label, sql in [('浏览','browse_history'),('收藏','favorite'),
        ('点赞','user_like'),('评论','news_comment'),
        ('帖子','community_post'),('AI','ai_generate_record')]:
        c.execute(f'SELECT COUNT(*) FROM {sql} WHERE user_id=%s', (uid,))
        stats[label] = c.fetchone()[0]
    print(f"  [{uid}] {nick}: 浏览{stats['浏览']} 收藏{stats['收藏']} 点赞{stats['点赞']} 评论{stats['评论']} 帖子{stats['帖子']} AI{stats['AI']}")

c.close()
print('\n完成!')
