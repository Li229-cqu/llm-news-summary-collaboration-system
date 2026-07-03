import json, random, pymysql
from datetime import datetime, timedelta

conn = pymysql.connect(host='127.0.0.1', port=3306, user='llm_news_user',
                       password='123456', database='llm_news_system',
                       charset='utf8mb4', autocommit=True)
c = conn.cursor()

c.execute("SELECT id, nickname FROM user WHERE role='user' AND id != 1")
users = [(r[0], r[1]) for r in c.fetchall()]

c.execute("SELECT id, title FROM news ORDER BY RAND() LIMIT 80")
news_list = [(r[0], r[1]) for r in c.fetchall()]

tags_pool = ['科技','编程','AI','阅读','生活','工具','前端','后端','算法','职业',
             '新闻','设计','产品','创业','云计算','安全','数据','开源','教育','游戏']

post_titles = [
    '如何看待AI在新闻行业的应用前景？','推荐几个优质的新闻聚合工具',
    '深度学习的入门路线应该怎么规划？','最近在读的一本好书分享',
    '前端框架Vue vs React，大家更倾向哪个？','Python后端开发的生态越来越好了',
    '分享一个实用的数据可视化技巧','大家平时用什么工具做笔记？',
    '关于大语言模型的一些思考','怎么提高自己的代码质量？',
    '有什么好的算法学习资源推荐吗？','聊聊微服务架构的优缺点',
    '数据库优化的一些经验分享','TypeScript值得学吗？',
    'AI辅助编程工具哪个最好用？','最近的热点新闻你们关注了吗？',
    '分享一个提高工作效率的小技巧','容器化部署的实践经验',
    'Rust语言未来会取代C++吗？','如何平衡工作和学习的时间？',
    '推荐几部好看的科幻电影','开源项目贡献的入门指南',
    '云原生技术栈的学习路径','对自动驾驶技术的一些看法',
    '量子计算的最新进展','网络安全入门应该从哪里开始？',
    '移动端开发框架的选择建议','程序员如何保持健康的身体？',
    'Kubernetes生产环境最佳实践','人工智能伦理问题大家怎么看？',
    '最近尝试了新的工作流分享一下','有没有好的项目管理方法推荐？',
    '远程办公的体验和心得','聊聊技术面试的那些事',
    '如何看待低代码平台的崛起？','分布式系统的设计原则',
]
post_contents = [
    '最近一直在思考这个问题，AI在新闻行业的应用确实越来越广泛了。从自动化写作到个性化推荐，AI正在改变我们获取信息的方式。但同时也带来了一些挑战，比如信息真实性的验证、算法偏见的防范等。',
    '用了几个月的各种新闻聚合工具，分享一下心得。Feedly适合RSS订阅，SmartNews的AI推荐做得不错，微信读书的新闻板块也挺好。你们有更好的推荐吗？',
    '作为一个过来人，建议从Python基础开始，然后学NumPy、Pandas做数据处理，接着入门scikit-learn，最后深入PyTorch或TensorFlow。关键是要多做项目。',
    '最近读了《人类简史》作者的新书，感触很深。书中探讨了AI时代人类面临的挑战和机遇。强烈推荐给大家，读完来讨论。',
    '用了Vue 3两年多，Composition API确实比Options API好用很多。但React的hooks也很灵活。其实选择哪个框架不重要，重要的是把项目做好。',
    'FastAPI + SQLAlchemy + Redis 这个组合真的很好用，开发效率高，性能也不错。最近还尝试了Django Ninja，也很喜欢。',
    '用ECharts做了一个数据大屏，效果真的很棒。关键是要先想清楚要表达什么信息，再选择合适的图表类型。少即是多。',
    '试过Notion、Obsidian、Logseq，最后选择了Obsidian。本地存储、双向链接、插件生态丰富，对程序员特别友好。',
    '大语言模型的涌现能力确实让人惊叹。但我觉得目前最大的挑战是幻觉问题和推理成本。未来几年应该会有更多突破。',
    '代码审查是最好的学习方式之一。另外写单元测试、阅读优秀开源代码、重构旧项目，都是提升代码质量的好方法。',
    'LeetCode刷了200题后的感悟：重要的是掌握解题思路而不是背答案。推荐《算法导论》和《剑指Offer》两本书。',
    '我们团队从单体架构迁移到微服务，虽然部署运维变复杂了，但开发效率和系统可扩展性提升明显。',
    '索引优化是数据库性能调优的重中之重。Explain分析执行计划、避免全表扫描、合理使用覆盖索引，这些基本功一定要扎实。',
    'TypeScript绝对是值得学的！类型安全让代码更健壮，IDE的智能提示也更准确。虽然上手有点陡峭，但一周就能适应。',
    'GitHub Copilot和Cursor都用过，各有优势。Copilot的上下文理解更强，Cursor的交互更友好。关键是它们能节省大量重复编码时间。',
    '最近国际局势变化很快，建议大家多看几个不同来源的报道，避免信息茧房。兼听则明，偏信则暗。',
    '番茄工作法真的很有效！25分钟专注工作加5分钟休息，一天下来效率提升明显。配合Forest App使用效果更好。',
    'Docker Compose + GitHub Actions + AWS ECS，这套CI/CD流水线搭起来后，部署效率提升了10倍。推荐大家都试试容器化。',
    'Rust的内存安全机制确实很先进，但学习曲线太陡了。C++在生态和人才储备上还有很大优势，短期内不会被取代。',
    '每天用Toggl记录时间开销，每周做一次回顾。发现自己在社交媒体上浪费了太多时间，正在努力减少。',
    '《星际穿越》《降临》《银翼杀手2049》这三部是我的科幻电影前三名。诺兰的叙事手法和视觉效果真的无人能敌。',
    '给Apache项目贡献代码的经历让我学到了很多：代码规范、沟通技巧、版本控制、持续集成。推荐有一定基础的同学尝试。',
    'K8s + Istio + Prometheus + Grafana + ELK，这套组合基本覆盖了微服务的部署、治理、监控和日志。',
    '自动驾驶L4级别在特定场景下已经可以实现，但大规模商用还有很长的路要走。技术、法规、伦理三个维度都需要突破。',
    '量子计算在密码学、药物研发、金融建模等领域前景广阔。但目前还处于早期阶段，距离实用化还需要时间。',
    '从OWASP Top 10开始学起，然后掌握Burp Suite和Nmap等工具，再深入了解Web安全和网络协议。CTF比赛是很好的实践方式。',
    'Flutter做跨平台移动开发效率真的高，一套代码同时出iOS和Android。虽然包体积大了点，但对于大多数项目来说完全可以接受。',
    '每天坚持站立办公2小时，中午去健身房30分钟，晚上11点前睡觉。坚持了半年，颈椎和腰椎的问题明显改善了。',
    'K8s生产环境要注意：资源限制、健康检查、滚动更新策略、Pod反亲和性、日志收集。这些基础做好了就行。',
    'AI伦理是一个需要全社会关注的话题。算法的公平性、透明度、问责制，以及对就业的影响，都需要深入讨论和制定规范。',
    '最近尝试了新的工作流：Linear管理任务加Notion记笔记加Slack沟通，效率翻倍。推荐给需要远程协作的团队。',
    '推荐《人月神话》和《代码大全》两本书，软件工程领域的经典之作。虽然出版有些年头了，但核心思想至今仍然适用。',
    '远程办公两年了，总结几个要点：规律作息、独立工作空间、定期视频交流团队。自律是最大的挑战。',
    '面试了50多人后的一些感想：基础知识扎实加上项目经验丰富加上沟通能力好等于好候选人。简历要突出自己做的项目。',
    '低代码平台确实降低了一些场景的开发门槛，但复杂的业务逻辑还是需要手写代码。选择合适的场景使用才是关键。',
    '分布式系统的CAP定理是基础，理解好它才能做好架构权衡。最终一致性是个好东西，但用错了场景会很麻烦。',
]

print('=== 修复帖子 (JSON格式 tags) ===')
for i in range(36):
    user_id, _ = random.choice(users)
    title = post_titles[i]
    content = post_contents[i]
    create_time = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
    tag_list = random.sample(tags_pool, random.randint(1, 3))
    tags_json = json.dumps(tag_list, ensure_ascii=False)
    try:
        c.execute(
            'INSERT INTO community_post (user_id, title, content, tags, view_count, like_count, comment_count, favorite_count, status, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1,%s,%s)',
            (user_id, title, content, tags_json, random.randint(30, 500), random.randint(0, 25), random.randint(0, 15), random.randint(0, 8), create_time, create_time),
        )
    except Exception as e:
        print(f'  帖子{i+1}跳过: {e}')
    if i % 10 == 0:
        print(f'  已处理 {i+1}/36')

print('\n=== 修复 AI记录 (JSON格式 titles) ===')
source_texts = [
    '人工智能技术在医疗领域的应用日益广泛。从辅助诊断到药物研发，AI正在改变传统医疗模式。',
    '新能源汽车市场持续增长，各大车企纷纷加大研发投入。今年上半年销量同比增长超过40%。',
    '随着5G技术的普及，物联网应用场景不断扩展。智能家居、智慧城市、工业互联网快速发展。',
    '在线教育行业经历了爆发式增长后进入调整期。教育科技公司正在探索线上线下融合的新模式。',
]
for i in range(25):
    user_id, _ = random.choice(users)
    source_text = random.choice(source_texts) + '\n\n' + random.choice(source_texts)
    n = random.choice(news_list)
    titles_json = json.dumps([f'随机标题{i}-A', f'随机标题{i}-B', f'随机标题{i}-C'], ensure_ascii=False)
    summary = '这是关于该新闻的AI生成摘要内容，总结了核心要点和关键信息。本文分析了多个维度的数据，得出了有价值的结论。'
    create_time = datetime.now() - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))
    try:
        c.execute(
            'INSERT INTO ai_generate_record (user_id, source, source_news_id, source_title, input_text, candidate_titles, summary_short, risk_level, status, create_time) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1,%s)',
            (user_id, 'news', n[0], n[1][:50], source_text, titles_json, summary, random.choice(['low','low','low','medium']), create_time),
        )
    except Exception as e:
        print(f'  AI记录{i+1}跳过: {e}')
    if i % 8 == 0:
        print(f'  已处理 {i+1}/25')

print('\n全部完成!')
c.close()
conn.close()
