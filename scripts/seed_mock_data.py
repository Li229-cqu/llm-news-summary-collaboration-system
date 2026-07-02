"""生成模拟互动数据：帖子、评论、收藏、点赞、浏览记录、AI记录等。
仅对普通用户生成（跳过 admin/editor），已有数据不删除。"""
import random
import pymysql
from datetime import datetime, timedelta

conn = pymysql.connect(
    host="127.0.0.1", port=3306, user="llm_news_user",
    password="123456", database="llm_news_system", charset="utf8mb4",
    autocommit=True,
)
c = conn.cursor()

# ── 1. 查用户和新闻 ──
c.execute("SELECT id, nickname FROM user WHERE role='user' AND id != 1")
users = [(r[0], r[1]) for r in c.fetchall()]  # id=5,6,7,8,9,10 (跳过id=1普通用户，保留其现有数据)

c.execute("SELECT id, title FROM news ORDER BY RAND() LIMIT 80")
news_list = [(r[0], r[1]) for r in c.fetchall()]

# 帖子标题库
post_titles = [
    "如何看待AI在新闻行业的应用前景？",
    "推荐几个优质的新闻聚合工具",
    "深度学习的入门路线应该怎么规划？",
    "最近在读的一本好书分享",
    "前端框架Vue vs React，大家更倾向哪个？",
    "Python后端开发的生态越来越好了",
    "分享一个实用的数据可视化技巧",
    "大家平时用什么工具做笔记？",
    "关于大语言模型的一些思考",
    "怎么提高自己的代码质量？",
    "有什么好的算法学习资源推荐吗？",
    "聊聊微服务架构的优缺点",
    "数据库优化的一些经验分享",
    "TypeScript值得学吗？",
    "AI辅助编程工具哪个最好用？",
    "最近的热点新闻你们关注了吗？",
    "分享一个提高工作效率的小技巧",
    "容器化部署的实践经验",
    "Rust语言未来会取代C++吗？",
    "如何平衡工作和学习的时间？",
    "推荐几部好看的科幻电影",
    "开源项目贡献的入门指南",
    "云原生技术栈的学习路径",
    "对自动驾驶技术的一些看法",
    "量子计算的最新进展",
    "网络安全入门应该从哪里开始？",
    "移动端开发框架的选择建议",
    "程序员如何保持健康的身体？",
    "Kubernetes生产环境最佳实践",
    "人工智能伦理问题大家怎么看？",
]
post_contents = [
    "最近一直在思考这个问题，AI在新闻行业的应用确实越来越广泛了。从自动化写作到个性化推荐，AI正在改变我们获取信息的方式。但同时也带来了一些挑战，比如信息真实性的验证、算法偏见的防范等。大家有什么看法？",
    "我用了几个月的各种新闻聚合工具，分享一下心得：1. Feedly适合RSS订阅；2. SmartNews的AI推荐做得不错；3. 微信读书的新闻板块也挺好。你们有更好的推荐吗？",
    "作为一个过来人，建议从Python基础开始，然后学NumPy、Pandas做数据处理，接着入门scikit-learn，最后深入PyTorch或TensorFlow。关键是要多做项目，理论结合实践。",
    "最近读了《人类简史》作者的新书，感触很深。书中探讨了AI时代人类面临的挑战和机遇。强烈推荐给大家，读完来讨论。",
    "用了Vue 3两年多了，Composition API确实比Options API好用很多。但React的hooks也很灵活。其实选择哪个框架不重要，重要的是把项目做好。",
    "FastAPI + SQLAlchemy + Redis 这个组合真的很好用，开发效率高，性能也不错。最近还尝试了Django Ninja，也很喜欢。",
    "用ECharts做了一个数据大屏，效果真的很棒。关键是要先想清楚要表达什么信息，再选择合适的图表类型。少即是多。",
    "试过Notion、Obsidian、Logseq，最后选择了Obsidian。本地存储、双向链接、插件生态丰富，对程序员特别友好。",
    "大语言模型的涌现能力确实让人惊叹。但我觉得目前最大的挑战是幻觉问题和推理成本。未来几年应该会有更多突破。",
    "代码审查是最好的学习方式之一。另外，写单元测试、阅读优秀开源代码、重构旧项目，都是提升代码质量的好方法。",
    "LeetCode刷了200题后的感悟：重要的是掌握解题思路而不是背答案。推荐《算法导论》和《剑指Offer》两本书。",
    "我们团队从单体架构迁移到微服务，虽然部署运维变复杂了，但开发效率和系统的可扩展性提升明显。关键是前期要做好服务边界的划分。",
    "索引优化是数据库性能调优的重中之重。Explain分析执行计划、避免全表扫描、合理使用覆盖索引，这些基本功一定要扎实。",
    "TypeScript绝对是值得学的！类型安全让代码更健壮，IDE的智能提示也更准确。虽然上手有点陡峭，但一周就能适应。",
    "GitHub Copilot和Cursor都用过，各有优势。Copilot的上下文理解更强，Cursor的交互更友好。关键是它们能节省大量重复编码时间。",
    "最近国际局势变化很快，建议大家多看几个不同来源的报道，避免信息茧房。兼听则明，偏信则暗。",
    "番茄工作法真的很有效！25分钟专注工作 + 5分钟休息，一天下来效率提升明显。配合Forest App使用效果更好。",
    "Docker Compose + GitHub Actions + AWS ECS，这套CI/CD流水线搭起来后，部署效率提升了10倍。推荐大家都试试容器化。",
    "Rust的内存安全机制确实很先进，但学习曲线太陡了。C++在生态和人才储备上还有很大优势，短期内不会被取代。",
    "每天用Toggl记录时间开销，每周做一次回顾。发现自己在社交媒体上浪费了太多时间，正在努力减少。",
    "《星际穿越》《降临》《银翼杀手2049》这三部是我的科幻电影前三名。诺兰的叙事手法和视觉效果真的无人能敌。",
    "给Apache项目贡献代码的经历让我学到了很多：代码规范、沟通技巧、版本控制、持续集成。推荐有一定基础的同学尝试。",
    "K8s + Istio + Prometheus + Grafana + ELK，这套组合基本覆盖了微服务的部署、治理、监控和日志。学起来确实有挑战但很值得。",
    "自动驾驶L4级别在特定场景下已经可以实现，但大规模商用还有很长的路要走。技术、法规、伦理三个维度都需要突破。",
    "量子计算在密码学、药物研发、金融建模等领域前景广阔。但目前还处于早期阶段，距离实用化还需要时间。",
    "从OWASP Top 10开始学起，然后掌握Burp Suite和Nmap等工具，再深入了解Web安全和网络协议。CTF比赛是很好的实践方式。",
    "Flutter做跨平台移动开发效率真的高，一套代码同时出iOS和Android。虽然包体积大了点，但对于大多数项目来说完全可以接受。",
    "每天坚持站立办公2小时，中午去健身房30分钟，晚上11点前睡觉。坚持了半年，颈椎和腰椎的问题明显改善了。",
    "K8s生产环境要注意：资源限制、健康检查、滚动更新策略、Pod反亲和性、日志收集。这些基础做好了，大部分问题都能避免。",
    "AI伦理是一个需要全社会关注的话题。算法的公平性、透明度、问责制，以及对人就业的影响，都需要深入讨论和制定规范。",
]

# ── 2. 生成帖子 ──
print("=== 生成社区帖子 ===")
for i in range(36):
    user_id, nickname = random.choice(users)
    title = post_titles[i % len(post_titles)]
    content = post_contents[i % len(post_contents)]
    create_time = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
    tags = random.sample(["科技", "编程", "AI", "阅读", "生活", "工具", "前端", "后端", "算法", "职业"], random.randint(1, 3))
    tag_str = ",".join(tags)
    view_count = random.randint(30, 500)
    like_count = random.randint(0, 25)
    comment_count = random.randint(0, 15)
    favorite_count = random.randint(0, 8)
    try:
        c.execute(
            "INSERT INTO community_post (user_id, title, content, tags, view_count, like_count, comment_count, favorite_count, status, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1,%s,%s)",
            (user_id, title, content, tag_str, view_count, like_count, comment_count, favorite_count, create_time, create_time),
        )
        if i % 10 == 0: print(f"  帖子 {i+1}/36")
    except Exception as e:
        print(f"  帖子跳过: {e}")

# ── 3. 帖子评论 ──
print("\n=== 生成帖子评论 ===")
c.execute("SELECT id, user_id FROM community_post WHERE id > 9")
posts = [(r[0], r[1]) for r in c.fetchall()]
comment_texts = [
    "写得很好，受益匪浅！", "这个观点我很赞同", "收藏了，慢慢看", "期待更多分享",
    "之前也遇到过类似的问题", "有没有更详细的教程？", "感谢分享！", "学习了，感谢！",
    "能不能再展开说说？", "和我的想法不谋而合", "这个工具确实好用", "推荐给同事们了",
    "已收藏，很有价值", "楼主能展开讲讲吗？", "写得不错，顶一个", "关注你了",
    "这个思路很新颖", "回去试试看", "非常好的总结", "期待下一篇",
]

for i in range(100):
    post = random.choice(posts)
    user_id, _ = random.choice(users)
    content = random.choice(comment_texts)
    create_time = datetime.now() - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))
    try:
        c.execute(
            "INSERT INTO post_comment (post_id, user_id, content, like_count, status, create_time) VALUES (%s,%s,%s,%s,1,%s)",
            (post[0], user_id, content, random.randint(0, 10), create_time),
        )
        if i % 20 == 0: print(f"  评论 {i+1}/100")
    except Exception as e:
        print(f"  评论跳过: {e}")

# ── 4. 新闻评论 ──
print("\n=== 生成新闻评论 ===")
news_comment_texts = [
    "这新闻写得不错", "有点意思", "值得关注", "终于看到相关报道了",
    "分析得很有道理", "关键还是要看后续发展", "不错，收藏了", "期待更多报道",
    "这个事件很重要", "有不同看法，但尊重作者观点", "信息量很大，慢慢消化",
    "感谢整理，很全面", "有些地方还需要核实", "写得挺客观的", "关注中",
    "这个角度很新颖", "数据很翔实", "已转发给朋友", "希望看到更多深度报道",
    "时事热点，关注了", "这篇报道挺及时的", "分析的逻辑很清晰", "认同作者的判断",
    "值得进一步讨论", "这个话题很火啊", "写得好，点赞", "持续关注中",
    "信息很有价值", "总结得很到位", "终于搞清楚了", "推荐大家看看",
]

for i in range(80):
    news = random.choice(news_list)
    user_id, _ = random.choice(users)
    content = random.choice(news_comment_texts)
    create_time = datetime.now() - timedelta(days=random.randint(0, 20), hours=random.randint(0, 23))
    try:
        c.execute(
            "INSERT INTO news_comment (news_id, user_id, content, like_count, status, create_time) VALUES (%s,%s,%s,%s,1,%s)",
            (news[0], user_id, content, random.randint(0, 8), create_time),
        )
        if i % 20 == 0: print(f"  评论 {i+1}/80")
    except Exception as e:
        print(f"  评论跳过: {e}")

# ── 5. 浏览记录 ──
print("\n=== 生成浏览记录 ===")
for i in range(200):
    user_id, _ = random.choice(users)
    if random.random() < 0.8:
        n = random.choice(news_list)
        try:
            c.execute("INSERT INTO browse_history (user_id, news_id, target_type, browse_time) VALUES (%s,%s,'news',%s)",
                      (user_id, n[0], datetime.now() - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))))
        except: pass
    else:
        if posts:
            p = random.choice(posts)
            try:
                c.execute("INSERT INTO browse_history (user_id, news_id, target_type, target_id, browse_time) VALUES (%s,0,'post',%s,%s)",
                          (user_id, p[0], datetime.now() - timedelta(days=random.randint(0, 14))))
            except: pass
    if i % 50 == 0: print(f"  记录 {i+1}/200")

# ── 6. 收藏 ──
print("\n=== 生成收藏 ===")
for i in range(80):
    user_id, _ = random.choice(users)
    if random.random() < 0.7:
        n = random.choice(news_list)
        try:
            c.execute("INSERT IGNORE INTO favorite (user_id, target_type, target_id, created_at) VALUES (%s,'news',%s,%s)",
                      (user_id, n[0], datetime.now() - timedelta(days=random.randint(0, 14))))
        except: pass
    else:
        if posts:
            p = random.choice(posts)
            try:
                c.execute("INSERT IGNORE INTO favorite (user_id, target_type, target_id, created_at) VALUES (%s,'post',%s,%s)",
                          (user_id, p[0], datetime.now() - timedelta(days=random.randint(0, 14))))
            except: pass
    if i % 20 == 0: print(f"  收藏 {i+1}/80")

# ── 7. 点赞 ──
print("\n=== 生成点赞 ===")
for i in range(100):
    user_id, _ = random.choice(users)
    if random.random() < 0.6:
        n = random.choice(news_list)
        try:
            c.execute("INSERT IGNORE INTO user_like (user_id, target_type, target_id, created_at) VALUES (%s,'news',%s,%s)",
                      (user_id, n[0], datetime.now() - timedelta(days=random.randint(0, 14))))
        except: pass
    else:
        if posts:
            p = random.choice(posts)
            try:
                c.execute("INSERT IGNORE INTO user_like (user_id, target_type, target_id, created_at) VALUES (%s,'post',%s,%s)",
                          (user_id, p[0], datetime.now() - timedelta(days=random.randint(0, 14))))
            except: pass
    if i % 25 == 0: print(f"  点赞 {i+1}/100")

# ── 8. AI 生成记录 ──
print("\n=== 生成AI生成记录 ===")
source_texts = [
    "人工智能技术在医疗领域的应用日益广泛，从辅助诊断到药物研发，AI正在改变传统医疗模式。据报道，多家医院已经开始使用AI辅助影像诊断系统，准确率达到95%以上。专家表示，未来AI将在个性化医疗和远程医疗方面发挥更大作用。",
    "新能源汽车市场持续增长，各大车企纷纷加大研发投入。据行业协会统计，今年上半年新能源汽车销量同比增长超过40%。充电基础设施的完善和电池技术的突破是推动市场增长的关键因素。政府出台了一系列支持政策，包括补贴和税收优惠。",
    "随着5G技术的普及，物联网应用场景不断扩展。智能家居、智慧城市、工业互联网等领域都迎来了快速发展期。据预测，到2025年全球物联网设备数量将超过250亿台。安全性是物联网发展面临的主要挑战之一。",
    "在线教育行业经历了爆发式增长后进入调整期。教育科技公司正在探索线上线下融合的新模式，AI个性化教学成为热门方向。数据显示，在线教育用户规模已超过4亿。内容质量和教学效果是用户最关注的指标。",
]
for i in range(25):
    user_id, _ = random.choice(users)
    source_text = random.choice(source_texts) + "\n\n" + random.choice(source_texts)
    n = random.choice(news_list)
    titles = [f"随机标题{i}-1", f"随机标题{i}-2", f"随机标题{i}-3"]
    summary = f"这是关于该新闻的AI生成摘要内容，总结了核心要点和关键信息。本文分析了多个维度的数据，得出了有价值的结论。"
    create_time = datetime.now() - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))
    try:
        c.execute(
            "INSERT INTO ai_generate_record (user_id, source, source_news_id, source_title, input_text, candidate_titles, summary_short, risk_level, status, create_time) VALUES (%s,'news',%s,%s,%s,%s,%s,%s,1,%s)",
            (user_id, n[0], n[1][:50], source_text, str(titles), summary, random.choice(["low", "low", "low", "medium"]), create_time),
        )
        if i % 8 == 0: print(f"  AI记录 {i+1}/25")
    except Exception as e:
        print(f"  AI记录跳过: {e}")

# ── 9. 更新帖子互动计数 ──
print("\n=== 更新帖子互动计数 ===")
c.execute("SELECT id FROM community_post")
for (pid,) in c.fetchall():
    c.execute("SELECT COUNT(*) FROM post_comment WHERE post_id=%s", (pid,))
    cc = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM user_like WHERE target_type='post' AND target_id=%s", (pid,))
    lc = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM favorite WHERE target_type='post' AND target_id=%s", (pid,))
    fc = c.fetchone()[0]
    c.execute("UPDATE community_post SET comment_count=%s, like_count=%s, favorite_count=%s WHERE id=%s", (cc, lc, fc, pid))

print("\n=== 全部完成 ===")
c.close()
conn.close()
