"""为 user_id=5 生成近 7 天演示行为数据。可重复执行（先清理旧数据）。"""
import pymysql, json, random
from datetime import datetime, timedelta

random.seed(42)

CONN = pymysql.connect(
    host='127.0.0.1', port=3306, user='llm_news_user', password='123456',
    database='llm_news_system', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor,
    autocommit=False,
)

USER_ID = 5
NOW = datetime(2026, 7, 1, 13, 0, 0)  # 以当前时间为准

def exec_sql(sql, params=None):
    with CONN.cursor() as c:
        c.execute(sql, params if params else ())
        return c.lastrowid

def query(sql, params=None):
    with CONN.cursor() as c:
        c.execute(sql, params if params else ())
        return c.fetchall()

# ============================================================
# 选定的新闻 ID（分类分布合理，标题有意义）
# ============================================================
NEWS_IDS = {
    'tech':     [1, 2, 943, 945],           # 科技
    'society':  [682, 683, 684, 685, 686],  # 社会
    'politics': [627, 628, 624],            # 时政
    'finance':  [3, 712, 713, 715],         # 财经
    'sports':   [742, 743],                 # 体育
    'entertainment': [793, 1001],           # 娱乐
}
ALL_NEWS = [nid for ids in NEWS_IDS.values() for nid in ids]

# 选定帖子 ID
POST_IDS = [1, 2, 3, 4, 5]

# ============================================================
# 时间分布：6天活跃（day 0=today 不活跃），晚上 19:00-23:00
# ============================================================
ACTIVE_DAYS = [1, 2, 3, 4, 5, 6]  # 近 6 天（跳过今天）
def rand_time(day_offset, hour_range=(19, 23)):
    """在指定天数前的指定小时范围内随机生成时间"""
    d = NOW - timedelta(days=day_offset)
    h = random.randint(*hour_range)
    m = random.randint(0, 59)
    s = random.randint(0, 59)
    return datetime(d.year, d.month, d.day, h, m, s)

print("=" * 60)
print("开始生成 user_id=5 演示数据")
print("=" * 60)

try:
    CONN.begin()
    print("\n[事务已开启]")

    # ========================================================
    # 1. 清理旧数据
    # ========================================================
    for tbl, cond in [
        ('browse_history', 'user_id=5'),
        ('favorite', 'user_id=5'),
        ('news_comment', "user_id=5"),
        ('post_comment', "user_id=5"),
        ('ai_generate_record', 'user_id=5'),
    ]:
        n = exec_sql(f'DELETE FROM {tbl} WHERE {cond}')
        print(f"  清理 {tbl}: {n} 行")

    # ========================================================
    # 2. 生成 browse_history（40条：33新闻 + 7帖子）
    # ========================================================
    browse_data = []

    # 新闻浏览：基础覆盖所有选中新闻（22条，每条1次）
    for i, nid in enumerate(ALL_NEWS):
        day = ACTIVE_DAYS[i % len(ACTIVE_DAYS)]
        browse_data.append({
            'user_id': USER_ID, 'news_id': nid,
            'target_type': 'news', 'target_id': None,
            'browse_time': rand_time(day),
            'created_at': rand_time(day),
        })

    # 新闻浏览：对重点新闻重复浏览（11条）
    re_browse = [1, 2, 943, 3, 712, 627, 684, 1, 2, 682, 945]  # 部分重复
    for nid in re_browse:
        day = random.choice(ACTIVE_DAYS)
        browse_data.append({
            'user_id': USER_ID, 'news_id': nid,
            'target_type': 'news', 'target_id': None,
            'browse_time': rand_time(day),
            'created_at': rand_time(day),
        })

    # 帖子浏览（7条，覆盖5个帖子，2个重复）
    post_browse_plan = [1, 2, 3, 1, 4, 5, 2]
    for pid in post_browse_plan:
        day = random.choice(ACTIVE_DAYS)
        browse_data.append({
            'user_id': USER_ID, 'news_id': 0,
            'target_type': 'post', 'target_id': pid,
            'browse_time': rand_time(day),
            'created_at': rand_time(day),
        })

    for b in browse_data:
        exec_sql(
            'INSERT INTO browse_history (user_id, news_id, target_type, target_id, browse_time, created_at) VALUES (%s,%s,%s,%s,%s,%s)',
            (b['user_id'], b['news_id'], b['target_type'], b['target_id'], b['browse_time'], b['created_at'])
        )
    print(f"  插入 browse_history: {len(browse_data)} 条")

    # ========================================================
    # 3. 生成 favorite（9条：7新闻 + 2帖子）
    # ========================================================
    fav_news = [1, 2, 943, 3, 627, 684, 712]   # 7条新闻收藏
    fav_posts = [1, 3]                            # 2条帖子收藏

    fav_data = []
    for nid in fav_news:
        day = random.choice(ACTIVE_DAYS)
        t = rand_time(day)
        fav_data.append({'user_id': USER_ID, 'target_type': 'news', 'target_id': nid, 'created_at': t, 'create_time': t})
    for pid in fav_posts:
        day = random.choice(ACTIVE_DAYS)
        t = rand_time(day)
        fav_data.append({'user_id': USER_ID, 'target_type': 'post', 'target_id': pid, 'created_at': t, 'create_time': t})

    for f in fav_data:
        exec_sql(
            'INSERT INTO favorite (user_id, target_type, target_id, created_at, create_time) VALUES (%s,%s,%s,%s,%s)',
            (f['user_id'], f['target_type'], f['target_id'], f['created_at'], f['create_time'])
        )
    print(f"  插入 favorite: {len(fav_data)} 条")

    # ========================================================
    # 4. 生成 news_comment（7条，status=1）
    # ========================================================
    news_comments = [
        (1, '【演示】这篇文章对AI技术应用的总结很到位，特别是企业转型部分，值得反复阅读。'),
        (2, '【演示】低空经济确实是下一个风口，无人机物流和城市空中交通都很值得关注。'),
        (943, '【演示】国产芯片的突破让人振奋，希望能尽快看到量产和应用落地。'),
        (3, '【演示】新能源市场的增长数据很有说服力，智能交通生态的构建思路清晰。'),
        (684, '【演示】数字化应急响应系统的建设太重要了，希望能推广到更多地区。'),
        (627, '【演示】核聚变如果能商用，能源格局将彻底改变，期待更多技术进展。'),
        (712, '【演示】认证检测行业的发展反映了产业升级的需求，数据很有参考价值。'),
    ]
    for nid, content in news_comments:
        day = random.choice(ACTIVE_DAYS)
        t = rand_time(day)
        exec_sql(
            'INSERT INTO news_comment (news_id, user_id, content, status, like_count, created_at, create_time, updated_at, update_time) VALUES (%s,%s,%s,1,0,%s,%s,%s,%s)',
            (nid, USER_ID, content, t, t, t, t)
        )
    print(f"  插入 news_comment: {len(news_comments)} 条")

    # ========================================================
    # 5. 生成 post_comment（4条，status=1）
    # ========================================================
    post_comments = [
        (1, '【演示】我个人习惯先看AI摘要再决定是否精读，效率确实提高了不少。'),
        (2, '【演示】无人机配送在郊区和中低空域的应用前景很好，希望能尽快规范化。'),
        (3, '【演示】数据可视化对于交通管理决策太关键了，期待看到更多实际案例。'),
        (4, '【演示】公共卫生事件的智能预警是AI落地的重要方向，技术已经比较成熟了。'),
    ]
    for pid, content in post_comments:
        day = random.choice(ACTIVE_DAYS)
        t = rand_time(day)
        exec_sql(
            'INSERT INTO post_comment (post_id, user_id, content, status, like_count, created_at, create_time, updated_at, update_time) VALUES (%s,%s,%s,1,0,%s,%s,%s,%s)',
            (pid, USER_ID, content, t, t, t, t)
        )
    print(f"  插入 post_comment: {len(post_comments)} 条")

    # ========================================================
    # 6. 生成 ai_generate_record（6条）
    # ========================================================
    ai_records = [
        {
            'source_title': '人工智能技术持续突破',
            'source_news_id': 1, 'source': 'news',
            'input_text': '人工智能技术正在加速渗透到各行各业，企业纷纷探索智能化转型路径。从制造业到医疗健康，AI应用场景不断拓展。',
            'candidate_titles': json.dumps(['AI技术加速企业智能化转型', '人工智能赋能千行百业', '智能时代的企业转型路径分析'], ensure_ascii=False),
            'summary_short': '本文分析了当前人工智能技术在企业智能化转型中的关键作用，指出AI正从概念验证走向规模化落地。',
            'summary_long': '人工智能技术正在各行各业加速落地。在制造业，AI质检和预测性维护显著降低成本；在医疗领域，AI辅助诊断提高准确率；在金融行业，智能风控和客服机器人提升效率。未来AI将进一步渗透更多垂直行业。',
            'risk_level': 'low',
        },
        {
            'source_title': '低空经济发展加速',
            'source_news_id': 2, 'source': 'news',
            'input_text': '低空经济正在快速发展，无人机配送、城市空中交通和农业植保等应用场景持续增加。',
            'candidate_titles': json.dumps(['低空经济加速起飞', '无人机应用场景持续扩展', '低空经济的新机遇与新挑战'], ensure_ascii=False),
            'summary_short': '低空经济正成为新增长引擎，无人机在物流、农业、安防等领域加速落地。',
            'summary_long': '低空经济作为新兴战略性产业，正在多领域展现巨大潜力。无人机配送在部分城市已实现常态化运营，农业植保无人机覆盖面积持续扩大，城市空中交通（UAM）的试点项目也在推进中。政策法规的完善将助推产业规范化发展。',
            'risk_level': 'low',
        },
        {
            'source_title': '国产芯片研发取得重要突破',
            'source_news_id': 943, 'source': 'news',
            'input_text': '国内首款高性能智能计算芯片研发成功，标志着国产芯片在AI推理领域迈出关键一步。',
            'candidate_titles': json.dumps(['国产高性能AI芯片取得突破', '首款国产智能计算芯片问世', '国产芯片在AI推理领域的里程碑'], ensure_ascii=False),
            'summary_short': '国内首款高性能智能计算芯片完成研发，在AI推理性能上达到国际主流水平。',
            'summary_long': '该芯片采用先进架构设计，在算力密度和能效比方面表现突出，可广泛应用于云端推理、边缘计算和自动驾驶等场景。此举将有效降低对进口芯片的依赖，推动国产AI生态建设。',
            'risk_level': 'low',
        },
        {
            'source_title': '新能源市场持续增长',
            'source_news_id': 3, 'source': 'news',
            'input_text': '新能源市场保持高速增长态势，智能交通生态系统正在加速形成，电动汽车和储能技术成为投资热点。',
            'candidate_titles': json.dumps(['新能源市场持续高速增长', '智能交通生态加速构建', '新能源与储能技术投资机遇'], ensure_ascii=False),
            'summary_short': '新能源市场在政策支持和资本推动下保持强劲增长，智能交通生态逐步完善。',
            'summary_long': '随着充电基础设施的完善和电池技术的进步，新能源汽车渗透率持续攀升。储能市场也迎来爆发期，锂电、钠电和液流电池等多技术路线并行发展。智能交通系统整合车路协同和大数据分析，为城市交通管理提供新方案。',
            'risk_level': 'low',
        },
        {
            'source_title': '核聚变研究取得重要进展',
            'source_news_id': 627, 'source': 'news',
            'input_text': '我国核聚变堆关键技术研发取得重要突破，等离子体约束时间创下新纪录。',
            'candidate_titles': json.dumps(['核聚变研究实现关键技术突破', '我国核聚变装置创运行新纪录', '可控核聚变离商用还有多远'], ensure_ascii=False),
            'summary_short': '我国核聚变实验装置在等离子体约束和加热效率方面取得重大进展。',
            'summary_long': '最新实验实现了更长的等离子体约束时间和更高的聚变功率输出，为未来聚变堆设计提供了关键数据。尽管商用聚变发电仍需较长时间，但每一次技术突破都在缩短这个距离。',
            'risk_level': 'medium',
        },
        {
            'source_title': '',
            'source_news_id': None, 'source': 'manual',
            'input_text': '我想了解最近科技领域有哪些值得关注的趋势，特别是人工智能、芯片和新能源方向的交叉发展。',
            'candidate_titles': json.dumps(['近期科技发展三大趋势分析', 'AI芯片与新能源的协同创新', '2026年科技产业投资方向梳理'], ensure_ascii=False),
            'summary_short': '当前科技产业呈现三大趋势：AI从模型竞赛转向应用落地，国产芯片加速追赶，新能源与智能技术深度融合。',
            'summary_long': '在人工智能领域，大模型正在从底层技术竞争转向行业应用落地，企业级AI解决方案成为新热点。芯片方面，国产AI推理芯片性能持续提升，与海外产品的差距不断缩小。新能源领域，AI技术在电池管理、电网调度和自动驾驶中的应用日益深入，三大技术方向正在形成协同效应。',
            'risk_level': 'low',
        },
    ]
    for r in ai_records:
        day = random.choice(ACTIVE_DAYS)
        t = rand_time(day)
        exec_sql(
            '''INSERT INTO ai_generate_record
               (user_id, source, source_news_id, source_title, input_text,
                candidate_titles, summary_short, summary_long, risk_level,
                status, ai_source, title_count, summary_type, summary_length,
                created_at, create_time, updated_at, update_time)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,1,'demo',3,'generate','both',%s,%s,%s,%s)''',
            (USER_ID, r['source'], r['source_news_id'], r['source_title'], r['input_text'],
             r['candidate_titles'], r['summary_short'], r['summary_long'], r['risk_level'],
             t, t, t, t)
        )
    print(f"  插入 ai_generate_record: {len(ai_records)} 条")

    # ========================================================
    # 7. 同步计数字段（仅涉及本次使用的 news_id 和 post_id）
    # ========================================================
    print("\n[同步计数字段]")
    affected_news = set()
    for b in browse_data:
        if b['target_type'] == 'news' and b['news_id'] > 0:
            affected_news.add(b['news_id'])
    for f in fav_data:
        if f['target_type'] == 'news':
            affected_news.add(f['target_id'])
    for nid, _ in news_comments:
        affected_news.add(nid)

    for nid in sorted(affected_news):
        vc = query('SELECT COUNT(*) AS cnt FROM browse_history WHERE news_id=%s AND target_type="news"', (nid,))[0]['cnt']
        fc = query('SELECT COUNT(*) AS cnt FROM favorite WHERE target_id=%s AND target_type="news"', (nid,))[0]['cnt']
        cc = query('SELECT COUNT(*) AS cnt FROM news_comment WHERE news_id=%s AND status<>4', (nid,))[0]['cnt']
        exec_sql('UPDATE news SET view_count=%s, favorite_count=%s, comment_count=%s WHERE id=%s',
                 (vc, fc, cc, nid))
    print(f"  同步 news 计数: {len(affected_news)} 条新闻")

    affected_posts = set()
    for b in browse_data:
        if b['target_type'] == 'post' and b['target_id']:
            affected_posts.add(b['target_id'])
    for f in fav_data:
        if f['target_type'] == 'post':
            affected_posts.add(f['target_id'])
    for pid, _ in post_comments:
        affected_posts.add(pid)

    for pid in sorted(affected_posts):
        vc = query('SELECT COUNT(*) AS cnt FROM browse_history WHERE target_id=%s AND target_type="post"', (pid,))[0]['cnt']
        fc = query('SELECT COUNT(*) AS cnt FROM favorite WHERE target_id=%s AND target_type="post"', (pid,))[0]['cnt']
        cc = query('SELECT COUNT(*) AS cnt FROM post_comment WHERE post_id=%s AND status<>4', (pid,))[0]['cnt']
        exec_sql('UPDATE community_post SET view_count=%s, favorite_count=%s, comment_count=%s WHERE id=%s',
                 (vc, fc, cc, pid))
    print(f"  同步 community_post 计数: {len(affected_posts)} 条帖子")

    # ========================================================
    # 8. 校验
    # ========================================================
    print("\n[数据校验]")
    bh_total = query('SELECT COUNT(*) AS cnt FROM browse_history WHERE user_id=5')[0]['cnt']
    bh_news_distinct = query('SELECT COUNT(DISTINCT news_id) AS cnt FROM browse_history WHERE user_id=5 AND news_id>0')[0]['cnt']
    bh_post_distinct = query('SELECT COUNT(DISTINCT target_id) AS cnt FROM browse_history WHERE user_id=5 AND target_type="post"')[0]['cnt']
    fav_total = query('SELECT COUNT(*) AS cnt FROM favorite WHERE user_id=5')[0]['cnt']
    nc_total = query('SELECT COUNT(*) AS cnt FROM news_comment WHERE user_id=5')[0]['cnt']
    pc_total = query('SELECT COUNT(*) AS cnt FROM post_comment WHERE user_id=5')[0]['cnt']
    ai_total = query('SELECT COUNT(*) AS cnt FROM ai_generate_record WHERE user_id=5')[0]['cnt']
    active_days = query('SELECT COUNT(DISTINCT DATE(browse_time)) AS cnt FROM browse_history WHERE user_id=5')[0]['cnt']

    print(f"  browse_history 总数:    {bh_total}")
    print(f"  去重新闻浏览数:         {bh_news_distinct}")
    print(f"  去重帖子浏览数:         {bh_post_distinct}")
    print(f"  favorite 总数:          {fav_total}")
    print(f"  news_comment 总数:      {nc_total}")
    print(f"  post_comment 总数:      {pc_total}")
    print(f"  ai_generate_record 总数:{ai_total}")
    print(f"  活跃天数:               {active_days}")

    # 新闻分类分布
    cat_dist = query('''
        SELECT nc.name, COUNT(DISTINCT bh.news_id) AS cnt
        FROM browse_history bh
        JOIN news n ON n.id=bh.news_id
        JOIN news_category nc ON nc.id=n.category_id
        WHERE bh.user_id=5 AND bh.news_id>0 AND bh.target_type='news'
        GROUP BY nc.id, nc.name ORDER BY cnt DESC
    ''')
    print("  新闻分类分布:")
    for r in cat_dist:
        print(f"    {r['name']}: {r['cnt']}")

    # 帖子标签分布
    tag_dist = query('''
        SELECT COALESCE(JSON_UNQUOTE(JSON_EXTRACT(cp.tags, '$[0]')), '社区帖子') AS tag, COUNT(DISTINCT bh.target_id) AS cnt
        FROM browse_history bh
        JOIN community_post cp ON cp.id=bh.target_id
        WHERE bh.user_id=5 AND bh.target_type='post'
        GROUP BY tag ORDER BY cnt DESC
    ''')
    print("  帖子标签分布:")
    for r in tag_dist:
        print(f"    {r['tag']}: {r['cnt']}")

    # 每日分布
    daily = query('''
        SELECT DATE(browse_time) AS dt, COUNT(*) AS cnt
        FROM browse_history WHERE user_id=5
        GROUP BY DATE(browse_time) ORDER BY dt
    ''')
    print("  每日浏览分布:")
    for r in daily:
        print(f"    {r['dt']}: {r['cnt']}")

    # 计数一致性抽查
    print("  计数一致性抽查:")
    for nid in [1, 2, 3]:
        n = query('SELECT view_count, favorite_count, comment_count FROM news WHERE id=%s', (nid,))[0]
        print(f"    news id={nid}: views={n['view_count']} favs={n['favorite_count']} comments={n['comment_count']}")

    # ========================================================
    # 9. 提交
    # ========================================================
    CONN.commit()
    print("\n✅ 事务已提交，所有数据生成完毕！")

except Exception as e:
    CONN.rollback()
    print(f"\n❌ 发生错误，已回滚: {e}")
    raise
finally:
    CONN.close()
