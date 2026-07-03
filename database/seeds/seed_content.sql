-- ============================================================
-- Seed Phase 2: 内容生成 (18贴 + 50新闻评论 + 20帖子评论)
-- 依赖: seed_users.sql (@cu1~@cu3 @au1~@au12 @pu1~@pu15 @ed @ad)
-- 比例: 浏览:评论:点赞:收藏 = 10:2:3:1
-- ============================================================
SET NAMES utf8mb4;

-- ============================================================
-- PART A: community_post (18条)
-- ============================================================

-- Core-1 陈思远: 2 posts (科技深度)
INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@cu1, 'AI新闻摘要技术深度评测：从关键词到语义理解的进化之路', '作为深度使用AI摘要功能三个月的用户，我观察到摘要质量经历了三个阶段：关键词提取→句法压缩→语义理解。目前的摘要已经能较好地把握文章主旨，但在专业术语和数据的准确性上还有提升空间。建议产品团队在财经类新闻中引入数值校验层。', 2, 1, '["AI评测","语义理解","技术进化"]', 1, '2026-06-15 10:00:00');
SET @p1 = LAST_INSERT_ID();

INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@cu1, '科技新闻信息密度的量化分析与阅读策略', '我统计了近期100篇科技新闻的信息密度（关键信息点/字数），发现AI类新闻的信息密度最高（约12%），硬件类最低（约6%）。对于高密度新闻，建议使用摘要+跳读的工作流；低密度新闻则适合全文通读。这个发现对优化阅读效率很有帮助。', 7, 1, '["信息密度","阅读策略","数据分析"]', 1, '2026-06-28 14:00:00');
SET @p2 = LAST_INSERT_ID();

-- Core-2 刘洋: 2 posts (社区/综合)
INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@cu2, '社区讨论质量提升指南：如何写一条有价值的评论', '在社区潜水+活跃了几个月，我发现高质量评论有三个特征：1)引用具体数据或来源；2)提供不同视角而不是简单附和；3)对作者的观点做建设性补充。我整理了这份指南，希望能帮助更多用户写出好评论。欢迎大家补充！', 1, 1, '["社区建设","评论质量","用户指南"]', 1, '2026-06-18 09:30:00');
SET @p3 = LAST_INSERT_ID();

INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@cu2, '从数据看社区：哪些话题最受欢迎？', '我手动统计了社区最近100个帖子的互动数据。科技类帖子平均获赞8.2个，社会类5.1个，体育类3.8个。但财经类帖子的评论深度最高（平均每条评论105字），说明小众但专业的讨论反而更优质。', NULL, NULL, '["数据分析","社区趋势","话题热度"]', 1, '2026-07-01 11:00:00');
SET @p4 = LAST_INSERT_ID();

-- Core-3 黄志明: 2 posts (时政/财经)
INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@cu3, '近期政策密集出台：背后的经济逻辑梳理', '从新能源税收优惠到外商投资开放，最近一个月出台的经济政策有一个共同逻辑：通过结构性减税引导产业升级，同时扩大开放吸引外资。我将这些政策按时间线和影响领域做了梳理，希望能帮大家看清政策脉络。', 304, 3, '["政策分析","经济逻辑","产业升级"]', 1, '2026-06-22 15:30:00');
SET @p5 = LAST_INSERT_ID();

INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@cu3, '全球通胀分化：对中国资产配置的启示', '对比了印尼、美国、欧洲的最新CPI数据后发现：东南亚国家通胀压力减轻，而欧美核心通胀仍然顽固。对投资者来说，这可能意味着资金将从高通胀地区流向政策空间更大的新兴市场。', 273, NULL, '["全球通胀","资产配置","投资策略"]', 1, '2026-06-30 16:00:00');
SET @p6 = LAST_INSERT_ID();

-- Active Users: 12 posts (每人1条)
INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@au1, '时政新闻读者应该具备的三个基本素养', '长期关注时政新闻，我认为读者需要：1)辨别信息源的可信度；2)理解政策出台的背景和博弈过程；3)区分事实报道和观点评论。这些素养在当前信息环境下越来越重要。', 295, NULL, '["时政阅读","信息素养","媒体素养"]', 1, '2026-06-16 08:00:00');
SET @p7 = LAST_INSERT_ID();

INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@au2, '从巴基斯坦局势看南亚地缘政治新变化', '巴基斯坦近期的安全事件不是孤立的，需要放在中巴经济走廊、阿富汗局势、以及大国博弈的框架下理解。我梳理了最近三个月南亚地区的五个关键事件，供大家参考。', 297, NULL, '["南亚地缘","巴基斯坦","国际关系"]', 1, '2026-06-20 10:00:00');
SET @p8 = LAST_INSERT_ID();

INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@au3, '新能源税收优惠对各细分赛道的影响分析', '减免政策对不同环节的影响差异很大：整车企业直接受益，电池厂商间接受益，充电桩运营商长期受益。我建了一个简单的分析框架，按短期/中期/长期三个维度评估了各赛道的受益程度。', 304, 3, '["新能源","投资分析","产业链"]', 1, '2026-06-25 14:00:00');
SET @p9 = LAST_INSERT_ID();

INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@au4, '极端天气频发：我们如何提升社会韧性？', '最近南方暴雨和北方高温同时出现，这不是巧合。气候变化正在加速极端天气的频率和强度。除了应急响应，我们更需要从城市规划、基础设施和公众意识三个层面提升社会韧性。', 299, NULL, '["极端天气","社会韧性","气候变化"]', 1, '2026-06-23 09:00:00');
SET @p10 = LAST_INSERT_ID();

INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@au5, '世界杯淘汰赛预测：基于数据的理性分析', '我用历史数据和本届小组赛的统计指标（xG、控球率、防守效率等）做了一个淘汰赛预测模型。瑞士的防守效率排名前三，但半决赛将是对他们真正的考验。欢迎大家来讨论和打脸！', 305, NULL, '["世界杯","数据预测","足球分析"]', 1, '2026-06-27 20:00:00');
SET @p11 = LAST_INSERT_ID();

INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@au6, '娱乐新闻为什么也需要深度阅读？', '很多人觉得娱乐新闻就是吃瓜，但其实娱乐产业背后涉及资本运作、文化输出、商业模式等深层话题。我尝试用"三层阅读法"来重新理解娱乐新闻：表层（事件本身）→中层（产业逻辑）→深层（文化意义）。', 5, NULL, '["娱乐产业","深度阅读","文化分析"]', 1, '2026-06-19 16:00:00');
SET @p12 = LAST_INSERT_ID();

INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@au7, '开源AI vs 闭源AI：技术路线的未来之争', '近期AI安全标准框架的发布引发了开源和闭源路线的新一轮讨论。我的观点是：在基础模型层面，开源能促进创新和透明度；但在关键应用领域（如医疗、金融），闭源+严格审计可能更合适。', 2, 1, '["AI开源","技术路线","安全标准"]', 1, '2026-06-21 11:00:00');
SET @p13 = LAST_INSERT_ID();

INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@au8, '跨学科阅读的意外收获：当科技遇到人文', '最近同时关注了AI技术和国际政治两个看似不相关的领域，意外发现它们在"信任构建"这个主题上有深刻共鸣。AI需要建立用户信任，国际关系需要建立国家间信任——底层逻辑惊人地相似。', NULL, NULL, '["跨学科","科技人文","信任构建"]', 1, '2026-06-29 10:00:00');
SET @p14 = LAST_INSERT_ID();

INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@au9, '怎样利用碎片时间高效阅读新闻？', '作为一个通勤时间较长的上班族，我摸索出了一套碎片化新闻阅读系统：早上通勤用语音听AI摘要→午休时精读1-2篇重点新闻→晚上用事件脉络功能回顾当日热点。每天只需40分钟就能保持信息更新。', NULL, NULL, '["阅读方法","时间管理","效率提升"]', 1, '2026-06-17 09:00:00');
SET @p15 = LAST_INSERT_ID();

INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@au10, '医疗健康类新闻：如何在信息噪音中找到可靠内容？', '健康类新闻是假消息的重灾区。我总结了三个验证方法：1)查证是否引用了权威医学期刊；2)看是否有临床数据支持；3)警惕标题党。同时推荐几个靠谱的医疗信息来源。', 300, NULL, '["健康新闻","信息验证","媒体素养"]', 1, '2026-06-24 11:00:00');
SET @p16 = LAST_INSERT_ID();

INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@au11, '绿色生活不只是口号：从新闻到行动的转化', '看了很多关于新能源和环保的新闻，我开始尝试在生活中实践：使用新能源车、减少一次性塑料、参与碳账户。三个月下来，碳足迹减少了约40%。新闻的价值不只是获取信息，更是促进行动。', 304, 3, '["绿色生活","碳足迹","行动实践"]', 1, '2026-06-30 08:00:00');
SET @p17 = LAST_INSERT_ID();

INSERT IGNORE INTO `community_post` (`user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`, `status`, `created_at`)
VALUES (@au12, '新法规解读：从新闻看法律变化的趋势', '最近关注到网络安全、AI监管和数据隐私领域的多项法规出台。从法律角度看，这些法规有一个共同特点：从事后追责转向事前预防。这是一个重要的监管范式转变。', 2, NULL, '["法律解读","监管趋势","网络安全"]', 1, '2026-06-26 14:00:00');
SET @p18 = LAST_INSERT_ID();

-- ============================================================
-- PART B: news_comment (~50条, 按10:2:3:1比例)
-- Viral news: #302 #304 #299 #295 #305 #283
-- ============================================================

-- Core-1 陈思远: 5 comments (深度技术评论)
INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (302, @cu1, NULL, '新能源税收优惠政策的力度超出预期，从产业经济学角度看，这是典型的"供给侧减税+需求侧补贴"组合拳。短期内会刺激Q3销量，长期则加速产业从政策驱动向市场驱动转型。建议关注整车企业的毛利率变化。', 1, '2026-06-12 09:30:00');
SET @nc1 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (304, @cu1, NULL, '这次政策文件的措辞值得仔细分析。"加快形成"和"推动建立"这两个动词的频率明显高于往年，说明决策层对新能源产业的紧迫感在增强。从技术路线看，纯电和混动并行的表述也意味着政策不再单一押注纯电路线。', 1, '2026-06-14 10:00:00');
SET @nc2 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (2, @cu1, NULL, 'AI安全标准框架的发布是一个里程碑事件。但我注意到框架中对于"可解释性"的要求还比较模糊——如何在模型复杂度和可解释性之间找到平衡，是下一步需要解决的技术难题。', 1, '2026-06-10 11:00:00');
SET @nc3 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (283, @cu1, NULL, '嫦娥六号在月球背面的采样是人类航天史上的首次，科学价值不可估量。月球背面的地质年龄比正面更古老，样本分析可能为我们揭示月球早期的演化历史。', 1, '2026-06-17 14:00:00');
SET @nc4 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (7, @cu1, NULL, 'AI新闻助手的落地应用确实令人振奋，但我们需要区分"辅助编辑"和"替代编辑"的边界。从目前的技术水平看，AI在事实核查和逻辑一致性方面还不够可靠，人机协作是最优模式。', 1, '2026-06-13 16:00:00');
SET @nc5 = LAST_INSERT_ID();

-- Core-2 刘洋: 5 comments (社区/社会视角)
INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (299, @cu2, NULL, '看到吉林暴雨的报道很揪心。从社会治理角度看，极端天气预警系统的覆盖面和响应速度还需要提升。希望受灾群众能尽快得到妥善安置。', 1, '2026-06-15 08:00:00');
SET @nc6 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (295, @cu2, NULL, '这篇讲话的核心信息是"坚定信心"和"团结奋斗"。在当前复杂的国际环境下，保持内需增长和社会稳定是最重要的政策目标。', 1, '2026-06-16 10:00:00');
SET @nc7 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (1, @cu2, NULL, 'AI产业应用的报道越来越多，但大部分还停留在"试点"阶段。真正的规模化落地需要解决三个问题：数据质量、业务整合和人才储备。', 1, '2026-06-09 13:00:00');
SET @nc8 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (302, @cu2, @nc1, '陈思远的分析很到位！补充一点：这次政策还有一个隐含信号——对充电桩基础设施的重视程度明显提高。充电便利性是影响消费者购买决策的关键因素之一。', 1, '2026-06-12 15:00:00');
SET @nc9 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (297, @cu2, NULL, '巴基斯坦的安全局势牵动整个南亚。从普通人的视角，我们希望和平与稳定能尽快恢复，让民众不再生活在恐惧之中。', 1, '2026-06-19 09:00:00');
SET @nc10 = LAST_INSERT_ID();

-- Core-3 黄志明: 5 comments (时政/财经深度)
INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (304, @cu3, NULL, '从宏观经济学角度看，这次新能源税收优惠是一举三得：促进消费、推动产业升级、助力双碳目标。但需要注意财政可持续性——减税政策的退出机制需要在方案设计阶段就考虑清楚。', 1, '2026-06-14 14:00:00');
SET @nc11 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (273, @cu3, NULL, '印尼CPI 3.34%低于预期，这对东南亚来说是积极信号。但我们需要关注核心通胀率（剔除食品和能源）的走势——如果核心通胀也在回落，央行才有真正的降息空间。', 1, '2026-06-16 11:00:00');
SET @nc12 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (302, @cu3, @nc1, '你们的分析都很有价值。我从政策比较的角度补充：对比2015年和2020年的两轮新能源激励政策，这次政策的精准度明显更高——不是"撒胡椒面"式的普惠补贴，而是聚焦在关键堵点上的精准施策。', 1, '2026-06-13 09:00:00');
SET @nc13 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (263, @cu3, NULL, '七一勋章的获得者都是各自领域的杰出代表。他们的共同特点是：长期坚持、默默奉献、在平凡岗位做出不平凡贡献。这些品质在任何时代都值得学习和传承。', 1, '2026-06-18 08:00:00');
SET @nc14 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (295, @cu3, @nc7, '刘洋说得很好。我补充一个历史视角：中国每个重大发展阶段的战略定力都是克服困难的关键。当前强调"坚定信心"不是口号，而是基于对自身发展阶段的清醒认识。', 1, '2026-06-17 09:00:00');
SET @nc15 = LAST_INSERT_ID();

-- Active Users: 25 comments (~2 each, 分布在 viral news)
INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (295, @au1, NULL, '从政策研究的视角，这次讲话释放的信号非常清晰：稳增长、促改革、防风险三者并重。在当前阶段，稳增长是首要任务。', 1, '2026-06-17 08:00:00');
SET @nc16 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (263, @au1, NULL, '勋章获得者的故事让我深受感动。媒体应该多报道这些平凡英雄的事迹，让正能量在社会上广泛传播。', 1, '2026-06-19 09:00:00');
SET @nc17 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (297, @au2, NULL, '巴基斯坦的安全形势确实令人担忧。从地缘经济角度看，中巴经济走廊沿线的安全是双方共同关切，相信两国会加强合作应对挑战。', 1, '2026-06-18 10:00:00');
SET @nc18 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (273, @au2, NULL, '印尼的数据给东南亚投资者带来了信心。相比欧美的高通胀，东南亚的货币政策和财政空间更具灵活性，这也是近年来外资流入东盟的重要原因。', 1, '2026-06-20 14:00:00');
SET @nc19 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (304, @au3, NULL, '作为财经分析从业者，我最关注的是政策执行层面的细节：减免额度如何计算、申请流程是否简化、地方配套政策何时出台。这些细节决定了政策的实际效果。', 1, '2026-06-15 10:00:00');
SET @nc20 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (302, @au3, @nc1, '陈思远的分析框架很专业。从投资实践角度补充：建议关注政策发布后一周内的股市反应，整车板块和电池板块的分化走势会揭示市场对政策的真实解读。', 1, '2026-06-13 11:00:00');
SET @nc21 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (299, @au4, NULL, '极端天气越来越多，我们的城市基础设施面临严峻考验。海绵城市建设和排水系统升级不能再拖了。', 1, '2026-06-16 10:00:00');
SET @nc22 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (293, @au4, NULL, '北京机场客流量创新高说明出行需求正在快速恢复。这对航空、旅游和酒店行业都是积极信号。', 1, '2026-06-20 09:00:00');
SET @nc23 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (305, @au5, NULL, '瑞士队的防守确实赏心悦目！他们的541阵型在转换进攻时非常高效，这是现代足球的发展趋势——防守不再是消极的，而是进攻的起点。', 1, '2026-06-21 21:00:00');
SET @nc24 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (306, @au5, NULL, 'WTT重庆站中国队的表现一如既往地稳定。乒乓球运动的全球化进程在加快，这对项目发展是好事，也给中国队带来了新的挑战。', 1, '2026-06-23 20:00:00');
SET @nc25 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (5, @au6, NULL, 'AI防诈系统确实很有必要。现在诈骗手段越来越高明，尤其是针对老年人的电信诈骗。希望这种技术能尽快普及。', 1, '2026-06-12 15:00:00');
SET @nc26 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (299, @au6, NULL, '看到南方暴雨的新闻很担心。希望大家都能平安度过汛期，也感谢奋战在防汛一线的工作人员。', 1, '2026-06-18 11:00:00');
SET @nc27 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (2, @au7, NULL, 'AI安全标准框架的发布是行业自律的重要一步。但标准制定只是开始，真正的挑战在于执行和监督——如何确保企业真正遵守标准？', 1, '2026-06-11 10:00:00');
SET @nc28 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (7, @au7, @nc5, '完全同意"人机协作"的定位。AI可以处理重复性的摘要生成工作，但深度分析和价值判断仍然需要人类编辑的把关。', 1, '2026-06-14 09:00:00');
SET @nc29 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (283, @au8, NULL, '嫦娥六号的成功让世界看到了中国航天的实力。从文化角度看，登月一直是人类的共同梦想，这次月背采样是全球科学界的财富。', 1, '2026-06-18 14:00:00');
SET @nc30 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (300, @au8, NULL, '中医和现代医学的结合是一个值得深入探讨的话题。新闻中提到"中西医协同"，这个方向是对的——不是相互排斥，而是取长补短。', 1, '2026-06-20 10:00:00');
SET @nc31 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (297, @au9, NULL, '国际新闻需要更多像这样的深度报道。单条新闻只能呈现事件的一个切面，而事件脉络功能能帮读者建立全局视角。', 1, '2026-06-19 15:00:00');
SET @nc32 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (300, @au10, NULL, '医疗健康领域的新闻需要更加审慎。这篇报道引用了具体数据和权威专家意见，值得肯定。建议后续跟进中西医结合治疗的长期效果评估。', 1, '2026-06-15 09:00:00');
SET @nc33 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (302, @au11, NULL, '从环保角度看，新能源车的推广不只是减少尾气排放，更重要的是推动整个能源结构从化石能源向清洁能源转型。每一个新能源车主都是这个转型的参与者。', 1, '2026-06-14 08:00:00');
SET @nc34 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (304, @au11, @nc11, '黄志明提到的财政可持续性很重要。我补充一个绿色金融视角：如果政策设计能引入碳信用机制，让新能源车主获得碳积分并交易，可以形成正向循环。', 1, '2026-06-16 15:00:00');
SET @nc35 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (2, @au12, NULL, 'AI安全标准从法律角度看有几个值得关注的要点：责任主体界定、跨境数据流动、以及算法歧视的认定标准。这些都是未来立法需要明确的问题。', 1, '2026-06-12 14:00:00');
SET @nc36 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (305, @au12, NULL, '从法律角度看，体育赛事的版权保护和反盗播是一个日益重要的话题。大型赛事的版权费用越来越高，需要更有效的法律手段来保护版权方的利益。', 1, '2026-06-22 10:00:00');
SET @nc37 = LAST_INSERT_ID();

-- Editor 赵立新: 3 comments (审稿视角)
INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (304, @ed, @nc11, '黄志明和各位的讨论质量很高。作为编辑，我在审稿时也会关注政策的长期影响和退出机制。后续我们会策划一组"新能源政策深度解读"专题，敬请关注。', 1, '2026-06-15 17:00:00');
SET @nc38 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (299, @ed, NULL, '编辑团队正在密切关注极端天气事件的报道。我们会优先发布权威气象部门的信息，并配合事件脉络功能帮读者了解灾情发展。大家有第一手信息也可以在评论区分享。', 1, '2026-06-16 14:00:00');
SET @nc39 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (2, @ed, @nc3, '陈思远和各位对AI安全的讨论给了编辑团队很大启发。我们会考虑在科技板块增加"AI治理"专栏，定期汇总全球AI监管动态。', 1, '2026-06-12 16:00:00');
SET @nc40 = LAST_INSERT_ID();

-- Admin 吴晓芳: 2 comments (运营视角)
INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (302, @ad, @nc1, '感谢陈思远和各位的深度讨论！看到新闻评论区的质量这么高，作为运营很欣慰。我们会把这条新闻标记为"精选内容"，让更多用户看到这些优质评论。', 1, '2026-06-13 15:00:00');
SET @nc41 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (283, @ad, NULL, '嫦娥六号成功采样是本月最重要的科技新闻之一。运营团队会在首页设置专题入口，并整理相关的事件脉络供大家参考。', 1, '2026-06-19 10:00:00');
SET @nc42 = LAST_INSERT_ID();

-- Passive users: 8 scattered comments
INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (302, @pu1, NULL, '这篇政策解读写得很清楚，终于看懂了新能源税收优惠的具体内容。', 1, '2026-06-15 11:00:00');
SET @nc43 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (299, @pu3, NULL, '希望灾区人民平安！', 1, '2026-06-17 12:00:00');
SET @nc44 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (305, @pu5, NULL, '瑞士踢得真好！这届世界杯冷门不少。', 1, '2026-06-22 20:30:00');
SET @nc45 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (304, @pu7, NULL, '希望新能源车越来越便宜，普通老百姓也能买得起。', 1, '2026-06-17 09:00:00');
SET @nc46 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (295, @pu9, NULL, '点赞！', 1, '2026-06-18 10:00:00');
SET @nc47 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (283, @pu11, NULL, '中国航天加油！', 1, '2026-06-20 15:00:00');
SET @nc48 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (306, @pu13, NULL, '乒乓球永远的神！', 1, '2026-06-24 19:00:00');
SET @nc49 = LAST_INSERT_ID();

INSERT IGNORE INTO `news_comment` (`news_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (297, @pu15, NULL, '希望世界和平。', 1, '2026-06-20 11:00:00');
SET @nc50 = LAST_INSERT_ID();

-- ============================================================
-- PART C: post_comment (~20条, 跨用户回复链)
-- ============================================================

-- 核心用户之间的互动
INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p1, @cu2, NULL, '陈思远的评测非常专业！我特别认同"数值校验层"的建议。财经类新闻的数据准确性确实是当前AI摘要最大的短板。', 1, '2026-06-16 10:30:00');
SET @pc1 = LAST_INSERT_ID();

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p1, @cu1, @pc1, '谢谢刘洋！数值校验其实可以从信息抽取环节开始做——在提取数字时保留上下文，而不是孤立地抓取。', 1, '2026-06-16 14:00:00');

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p3, @cu1, NULL, '刘洋这份指南太实用了！我特别同意第三条：建设性补充比简单附和更有价值。社区需要更多这样的"增量讨论"。', 1, '2026-06-19 10:00:00');
SET @pc3 = LAST_INSERT_ID();

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p3, @cu2, @pc3, '谢谢陈思远！你之前在我的帖子下的评论就是一个很好的"建设性补充"范例。希望更多用户能参与进来。', 1, '2026-06-19 15:00:00');

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p5, @cu1, NULL, '黄志明的政策梳理做得很清晰。建议可以再加上一个"政策力度评分"维度，帮助读者快速判断每条政策的重要性。', 1, '2026-06-23 10:00:00');

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p5, @cu3, NULL, '感谢陈思远的建议。"政策力度评分"这个想法很好，下次更新时我会加入这个维度。', 1, '2026-06-23 14:00:00');

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p9, @cu3, NULL, '孙浩然的分析框架很不错！从短期/中期/长期三个维度评估受益程度是个实用的方法论。我建议再加一个"不确定性"维度——政策执行过程中的变数也需要考虑。', 1, '2026-06-26 10:00:00');

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p9, @au3, NULL, '谢谢黄志明！"不确定性"维度确实很重要，尤其是地方配套政策的出台节奏往往不一致。', 1, '2026-06-26 15:00:00');

-- 活跃用户之间的互动
INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p8, @au1, NULL, '钱雪梅的南亚分析很到位。我补充一个角度：中巴经济走廊不仅是经济项目，更是区域治理模式的探索。', 1, '2026-06-21 09:00:00');
SET @pc9 = LAST_INSERT_ID();

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p8, @au2, @pc9, '赵文博的补充很精彩！区域治理模式的探索确实是走廊项目更深层的意义。', 1, '2026-06-21 14:00:00');

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p10, @au8, NULL, '周丽华关于社会韧性的讨论很有价值。从跨界视角看，社会韧性不只是基础设施的问题，还包括信息传播效率、社区互助网络等软性因素。', 1, '2026-06-24 10:00:00');

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p13, @au12, NULL, '马天宇关于开源vs闭源的讨论很有意思。从法律角度看，开源AI的许可证选择和责任豁免是未来立法需要重点考虑的问题。', 1, '2026-06-22 14:00:00');

-- 编辑/管理参与
INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p3, @ed, NULL, '刘洋的评论指南写得很专业！编辑团队也一直在思考如何提升社区讨论质量。我们会参考你的建议，优化评论区的引导机制。', 1, '2026-06-20 09:00:00');

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p4, @ad, NULL, '刘洋的数据分析对运营团队很有参考价值。我们后台看到的数据和你手动统计的趋势基本一致：科技和财经类内容虽然总量不多，但互动质量确实最高。', 1, '2026-07-02 10:00:00');

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p11, @au4, NULL, '虽然我不太懂足球，但这个预测模型的方法论可以应用到其他领域！比如天气预报的准确率评估也可以用类似的逻辑。', 1, '2026-06-28 10:00:00');
SET @pc15 = LAST_INSERT_ID();

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p11, @au5, @pc15, '跨领域应用是个很好的思路！体育数据分析的很多方法确实可以迁移到其他领域。', 1, '2026-06-28 16:00:00');

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p17, @au10, NULL, '高远的绿色生活实践太鼓舞人了！减少40%碳足迹的数据让我也想开始记录自己的碳足迹了。', 1, '2026-07-01 09:00:00');

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p2, @au7, NULL, '信息密度的分析角度很新颖！我也有类似的感受——AI论文的信息密度确实远高于产品发布类新闻。', 1, '2026-06-29 10:00:00');

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p14, @au9, NULL, '林雪芬的跨界观察太妙了！"信任构建"这个连接点让我对AI和国际关系都有了新的理解。', 1, '2026-06-30 09:00:00');

INSERT IGNORE INTO `post_comment` (`post_id`, `user_id`, `parent_id`, `content`, `status`, `created_at`)
VALUES (@p18, @cu3, NULL, '段明哲关于监管范式转变的观点很深刻。从事后追责到事前预防，这确实是一个结构性变化，对企业的合规成本影响很大。', 1, '2026-06-27 15:00:00');

SELECT 'seed_content.sql completed: 18 posts + 50 news comments + 20 post comments' AS status;
