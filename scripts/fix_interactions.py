"""针对性生成：让每个用户的帖子收到别人的点赞、评论、收藏"""
import random, pymysql, json
from datetime import datetime, timedelta

conn = pymysql.connect(host='127.0.0.1', port=3306, user='llm_news_user',
    password='123456', database='llm_news_system', charset='utf8mb4', autocommit=True)
c = conn.cursor()

# 普通用户列表（排除 id=1 的普通用户）
c.execute("SELECT id, nickname FROM user WHERE role='user' AND id IN (5,6,7,8,9,10)")
users = [(r[0], r[1]) for r in c.fetchall()]

comment_texts = [
    "写得很好，受益匪浅！", "这个观点我很赞同", "收藏了，慢慢看",
    "期待更多分享", "之前也遇到过类似的问题", "有没有更详细的教程？",
    "感谢分享！", "学习了，感谢！", "能不能再展开说说？",
    "和我的想法不谋而合", "这个思路很新颖", "回去试试看",
    "非常好的总结", "期待下一篇", "写得不错，顶一个",
    "关注你了", "这个工具确实好用", "已收藏转发",
    "有不同看法，但尊重作者观点", "这个话题很值得讨论",
    "信息量很大，慢慢消化", "写得太好了，学到了很多",
    "感谢整理，很全面", "分析的逻辑很清晰", "很好的入门指南",
]

print('=== 为每个用户的帖子生成别人互动 ===')
for post_owner_id, _ in users:
    # 其他人的ID
    other_users = [u for u in users if u[0] != post_owner_id]

    c.execute("SELECT id FROM community_post WHERE user_id=%s AND status=1", (post_owner_id,))
    posts = [r[0] for r in c.fetchall()]

    for pid in posts:
        # 2-5个其他人点赞
        n_likes = random.randint(2, min(5, len(other_users)))
        likers = random.sample(other_users, n_likes)
        for liker_id, _ in likers:
            try:
                c.execute("INSERT IGNORE INTO user_like (user_id, target_type, target_id, created_at) VALUES (%s,%s,%s,%s)",
                    (liker_id, 'post', pid, datetime.now() - timedelta(days=random.randint(0, 10), hours=random.randint(0, 23))))
            except: pass

        # 1-4个其他人评论
        n_comments = random.randint(1, min(4, len(other_users)))
        commenters = random.sample(other_users, n_comments)
        for commenter_id, _ in commenters:
            try:
                c.execute("INSERT INTO post_comment (post_id, user_id, content, like_count, status, create_time) VALUES (%s,%s,%s,%s,1,%s)",
                    (pid, commenter_id, random.choice(comment_texts), random.randint(0, 5),
                     datetime.now() - timedelta(days=random.randint(0, 10), hours=random.randint(0, 23))))
            except: pass

        # 1-3个其他人收藏
        n_favs = random.randint(1, min(3, len(other_users)))
        favoriters = random.sample(other_users, n_favs)
        for faver_id, _ in favoriters:
            try:
                c.execute("INSERT IGNORE INTO favorite (user_id, target_type, target_id, created_at) VALUES (%s,%s,%s,%s)",
                    (faver_id, 'post', pid, datetime.now() - timedelta(days=random.randint(0, 10))))
            except: pass

# 更新帖子互动计数
print('=== 更新帖子计数 ===')
c.execute("SELECT id FROM community_post")
for (pid,) in c.fetchall():
    c.execute("SELECT COUNT(*) FROM post_comment WHERE post_id=%s", (pid,))
    cc = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM user_like WHERE target_type='post' AND target_id=%s", (pid,))
    lc = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM favorite WHERE target_type='post' AND target_id=%s", (pid,))
    fc = c.fetchone()[0]
    c.execute("UPDATE community_post SET comment_count=%s, like_count=%s, favorite_count=%s WHERE id=%s", (cc, lc, fc, pid))

# 验证
print('\n=== 验证结果 ===')
for uid, nick in users:
    c.execute("SELECT COUNT(*) FROM community_post WHERE user_id=%s", (uid,))
    pc = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM user_like WHERE target_type='post' AND target_id IN (SELECT id FROM community_post WHERE user_id=%s) AND user_id!=%s", (uid, uid))
    lks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM post_comment WHERE post_id IN (SELECT id FROM community_post WHERE user_id=%s) AND user_id!=%s", (uid, uid))
    cmts = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM favorite WHERE target_type='post' AND target_id IN (SELECT id FROM community_post WHERE user_id=%s) AND user_id!=%s", (uid, uid))
    fvs = c.fetchone()[0]
    print(f"  [{uid}] {nick}: {pc}帖 -> 别人赞{lks} 评{cmts} 藏{fvs}")

c.close()
conn.close()
print('\n完成!')
