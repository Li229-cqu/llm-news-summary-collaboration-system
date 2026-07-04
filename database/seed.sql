  -- =========================================================
-- 《基于大语言模型的智能新闻摘要与协同互动系统》
-- 基础种子数据
-- =========================================================

SET NAMES utf8mb4;

-- 用户
INSERT INTO `user` (`id`, `username`, `password`, `nickname`, `role`, `avatar`, `status`)
VALUES
  (1, 'user', '123456', '普通用户', 'user', '', 1),
  (2, 'editor', '123456', '审核编辑', 'editor', '', 1),
  (3, 'admin', '123456', '系统管理员', 'admin', '', 1)
ON DUPLICATE KEY UPDATE
  `password` = VALUES(`password`),
  `nickname` = VALUES(`nickname`),
  `role` = VALUES(`role`),
  `status` = VALUES(`status`);

-- 新闻分类
INSERT INTO `news_category` (`id`, `name`, `code`, `description`, `sort`, `status`)
VALUES
  (1, '推荐', 'recommend', '推荐新闻', 1, 1),
  (2, '时政', 'politics', '时政新闻', 2, 1),
  (3, '社会', 'society', '社会新闻', 3, 1),
  (4, '财经', 'finance', '财经新闻', 4, 1),
  (5, '科技', 'technology', '科技新闻', 5, 1),
  (6, '体育', 'sports', '体育新闻', 6, 1),
  (7, '娱乐', 'entertainment', '娱乐新闻', 7, 1),
  (8, '国际', 'world', '国际新闻', 8, 1)
ON DUPLICATE KEY UPDATE
  `name` = VALUES(`name`),
  `description` = VALUES(`description`),
  `sort` = VALUES(`sort`),
  `status` = VALUES(`status`);

-- Timeline 话题
INSERT INTO `news_topic` (`id`, `topic_name`, `summary`, `keyword_list`, `heat_score`, `status`)
VALUES
  (1, '人工智能技术发展', '围绕人工智能、大模型、智能应用等方向的相关新闻事件脉络。', JSON_ARRAY('人工智能', '大模型', 'AI', '智能应用'), 100, 1),
  (2, '低空经济与无人机产业', '围绕低空经济、无人机产业、空域管理等方向的相关新闻事件脉络。', JSON_ARRAY('低空经济', '无人机', '空域', '飞行器'), 80, 1),
  (3, '新能源汽车与智能交通', '围绕新能源汽车、智能驾驶、交通出行等方向的相关新闻事件脉络。', JSON_ARRAY('新能源汽车', '智能交通', '自动驾驶', '充电'), 70, 1)
ON DUPLICATE KEY UPDATE
  `topic_name` = VALUES(`topic_name`),
  `summary` = VALUES(`summary`),
  `keyword_list` = VALUES(`keyword_list`),
  `heat_score` = VALUES(`heat_score`),
  `status` = VALUES(`status`);

-- 基础新闻数据
INSERT INTO `news` (
  `id`, `title`, `summary`, `content`, `cover_image`,
  `category_id`, `topic_id`, `source`, `editor`, `publish_time`,
  `source_url`, `view_count`, `like_count`, `comment_count`, `favorite_count`,
  `tags`, `status`
)
VALUES
  (
    1,
    '人工智能技术加速落地，多行业探索智能化转型',
    '人工智能技术正在从模型能力展示走向产业应用，多个行业开始探索智能化升级路径。',
    '近年来，人工智能技术快速发展，大模型、智能问答、内容生成和数据分析等能力逐渐进入实际业务场景。在新闻、教育、医疗、制造和交通等领域，相关企业和机构正在探索如何利用人工智能提高效率、降低成本并改善用户体验。业内人士认为，随着基础设施、算法能力和应用生态不断完善，人工智能将进一步推动各行业数字化转型。',
    '',
    5,
    1,
    '系统示例数据',
    '',
    '2026-01-01 09:00:00',
    'https://example.com/news/ai-1',
    120,
    8,
    2,
    5,
    JSON_ARRAY('人工智能', '大模型', '产业应用'),
    1
  ),
  (
    2,
    '低空经济发展提速，无人机应用场景不断拓展',
    '低空经济成为新兴产业关注点，无人机物流、巡检、测绘等应用不断扩展。',
    '随着相关政策和基础设施不断完善，低空经济正在成为多个地区培育新质生产力的重要方向。无人机在物流配送、农业植保、应急救援、电力巡检和城市治理等场景中展现出较强应用价值。专家表示，低空经济的发展需要统筹空域管理、飞行安全、产业标准和商业模式创新。',
    '',
    5,
    2,
    '系统示例数据',
    '',
    '2026-01-02 10:00:00',
    'https://example.com/news/drone-1',
    95,
    6,
    1,
    3,
    JSON_ARRAY('低空经济', '无人机', '产业发展'),
    1
  ),
  (
    3,
    '新能源汽车市场持续增长，智能交通生态加快形成',
    '新能源汽车销量增长带动充电、智能驾驶和交通服务生态持续完善。',
    '新能源汽车产业近年来保持较快发展，带动动力电池、充电基础设施、智能驾驶和车联网等相关产业协同升级。随着车辆智能化水平提升，交通管理、能源补给和出行服务也在发生变化。业内认为，新能源汽车与智能交通的结合将推动城市交通系统更加高效和低碳。',
    '',
    4,
    3,
    '系统示例数据',
    '',
    '2026-01-03 11:00:00',
    'https://example.com/news/ev-1',
    88,
    5,
    1,
    2,
    JSON_ARRAY('新能源汽车', '智能交通', '低碳出行'),
    1
  )
ON DUPLICATE KEY UPDATE
  `title` = VALUES(`title`),
  `summary` = VALUES(`summary`),
  `content` = VALUES(`content`),
  `category_id` = VALUES(`category_id`),
  `topic_id` = VALUES(`topic_id`),
  `source` = VALUES(`source`),
  `publish_time` = VALUES(`publish_time`),
  `source_url` = VALUES(`source_url`),
  `tags` = VALUES(`tags`),
  `status` = VALUES(`status`);

-- 基础评论
INSERT INTO `news_comment` (`id`, `news_id`, `user_id`, `parent_id`, `content`, `like_count`, `status`)
VALUES
  (1, 1, 1, NULL, '这条新闻对人工智能产业应用的说明比较清楚。', 2, 1),
  (2, 1, 2, NULL, '后续可以继续关注大模型在新闻行业中的应用。', 1, 1),
  (3, 2, 1, NULL, '低空经济确实是一个很有潜力的方向。', 1, 1)
ON DUPLICATE KEY UPDATE
  `content` = VALUES(`content`),
  `like_count` = VALUES(`like_count`),
  `status` = VALUES(`status`);

-- 热搜
INSERT INTO `hot_topic` (`id`, `title`, `target_type`, `target_id`, `heat_score`, `rank_no`, `tag`, `status`)
VALUES
  (1, '人工智能技术发展', 'news_topic', 1, 100, 1, '科技', 1),
  (2, '低空经济与无人机产业', 'news_topic', 2, 80, 2, '产业', 1),
  (3, '新能源汽车与智能交通', 'news_topic', 3, 70, 3, '财经', 1)
ON DUPLICATE KEY UPDATE
  `title` = VALUES(`title`),
  `target_type` = VALUES(`target_type`),
  `target_id` = VALUES(`target_id`),
  `heat_score` = VALUES(`heat_score`),
  `rank_no` = VALUES(`rank_no`),
  `tag` = VALUES(`tag`),
  `status` = VALUES(`status`);

-- Timeline 缓存
INSERT INTO `event_timeline` (`id`, `topic_id`, `timeline_json`, `source_news_ids`, `generate_status`)
VALUES
  (
    1,
    1,
    JSON_ARRAY(
      JSON_OBJECT(
        'event_id', 1,
        'event_time', '2026-01-01 09:00:00',
        'event_title', '人工智能技术加速落地',
        'event_summary', '多行业开始探索人工智能技术在业务场景中的应用。',
        'source_news_id', 1,
        'source_title', '人工智能技术加速落地，多行业探索智能化转型',
        'source_name', '系统示例数据'
      )
    ),
    JSON_ARRAY(1),
    'success'
  )
ON DUPLICATE KEY UPDATE
  `timeline_json` = VALUES(`timeline_json`),
  `source_news_ids` = VALUES(`source_news_ids`),
  `generate_status` = VALUES(`generate_status`);

-- 浏览历史
INSERT INTO `browse_history` (`id`, `user_id`, `news_id`, `browse_time`)
VALUES
  (1, 1, 1, '2026-01-15 10:30:00'),
  (2, 1, 2, '2026-01-15 11:20:00'),
  (3, 1, 3, '2026-01-16 09:15:00'),
  (4, 2, 1, '2026-01-14 14:00:00'),
  (5, 2, 3, '2026-01-15 16:45:00')
ON DUPLICATE KEY UPDATE
  `browse_time` = VALUES(`browse_time`);

-- 收藏记录
INSERT INTO `favorite` (`id`, `user_id`, `target_type`, `target_id`, `created_at`)
VALUES
  (1, 1, 'news', 1, '2026-01-15 10:45:00'),
  (2, 1, 'news', 3, '2026-01-16 09:30:00'),
  (3, 2, 'news', 2, '2026-01-15 12:00:00')
ON DUPLICATE KEY UPDATE
  `created_at` = VALUES(`created_at`);

-- AI生成记录
INSERT INTO `ai_generate_record` (
  `id`, `user_id`, `source`, `source_news_id`, `source_title`,
  `input_text`, `title_count`, `summary_type`, `summary_style`,
  `candidate_titles`, `summary_short`, `summary_long`,
  `summary_points`, `keywords`, `risk_level`, `status`, `created_at`
)
VALUES
  (
    1, 1, 'news', 1, '人工智能技术加速落地，多行业探索智能化转型',
    '人工智能技术正在从模型能力展示走向产业应用，多个行业开始探索智能化升级路径。',
    3, 'generate', 'formal',
    JSON_ARRAY(
      '人工智能技术加速落地，多行业探索智能化转型',
      'AI产业应用深入推进，各行业加速智能化升级',
      '大模型走向实际场景，人工智能推动产业变革'
    ),
    '人工智能技术正从模型展示走向产业应用，新闻、教育、医疗、制造、交通等多领域开始探索智能化升级，有望推动各行业数字化转型。',
    '近年来，人工智能技术快速发展，大模型、智能问答、内容生成和数据分析等能力逐渐进入实际业务场景。在新闻、教育、医疗、制造和交通等领域，相关企业和机构正在探索如何利用人工智能提高效率、降低成本并改善用户体验。业内人士认为，随着基础设施、算法能力和应用生态不断完善，人工智能将进一步推动各行业数字化转型。',
    JSON_ARRAY(
      '人工智能技术快速发展，大模型等能力进入实际业务场景',
      '新闻、教育、医疗、制造、交通等多领域探索智能化应用',
      '基础设施、算法能力和应用生态完善将推动产业数字化转型'
    ),
    JSON_ARRAY('人工智能', '大模型', '智能化转型', '产业应用'),
    'low', 1, '2026-01-15 11:00:00'
  ),
  (
    2, 1, 'news', 2, '低空经济发展提速，无人机应用场景不断拓展',
    '低空经济成为新兴产业关注点，无人机物流、巡检、测绘等应用不断扩展。',
    3, 'generate', 'concise',
    JSON_ARRAY(
      '低空经济发展提速，无人机应用场景不断拓展',
      '无人机应用持续扩展，低空经济迎来发展机遇',
      '政策基础设施逐步完善，低空经济蓄势待发'
    ),
    '低空经济正成为新质生产力重要方向，无人机在物流、植保、救援、巡检、城市治理等场景应用价值凸显，需统筹空域管理、飞行安全、产业标准和商业模式创新。',
    '随着相关政策和基础设施不断完善，低空经济正在成为多个地区培育新质生产力的重要方向。无人机在物流配送、农业植保、应急救援、电力巡检和城市治理等场景中展现出较强应用价值。专家表示，低空经济的发展需要统筹空域管理、飞行安全、产业标准和商业模式创新。',
    JSON_ARRAY(
      '政策基础设施完善推动低空经济成为新质生产力方向',
      '无人机在物流、植保、救援、巡检等多场景展现应用价值',
      '低空经济发展需统筹空域管理、安全、标准和商业模式'
    ),
    JSON_ARRAY('低空经济', '无人机', '产业发展', '空域管理'),
    'low', 1, '2026-01-16 10:00:00'
  ),
  (
    3, 2, 'news', 3, '新能源汽车市场持续增长，智能交通生态加快形成',
    '新能源汽车销量增长带动充电、智能驾驶和交通服务生态持续完善。',
    3, 'generate', 'formal',
    JSON_ARRAY(
      '新能源汽车市场持续增长，智能交通生态加快形成',
      '新能源汽车产业协同升级，智能交通生态逐步完善',
      '新能源车带动产业链发展，智慧交通系统加速构建'
    ),
    '新能源汽车产业快速发展，带动动力电池、充电基础设施、智能驾驶和车联网等产业协同升级，推动城市交通系统更加高效和低碳。',
    '新能源汽车产业近年来保持较快发展，带动动力电池、充电基础设施、智能驾驶和车联网等相关产业协同升级。随着车辆智能化水平提升，交通管理、能源补给和出行服务也在发生变化。业内认为，新能源汽车与智能交通的结合将推动城市交通系统更加高效和低碳。',
    JSON_ARRAY(
      '新能源汽车产业快速发展，带动相关产业协同升级',
      '车辆智能化推动交通管理、能源补给和出行服务变革',
      '新能源汽车与智能交通结合推动城市交通高效低碳发展'
    ),
    JSON_ARRAY('新能源汽车', '智能交通', '低碳出行', '车联网'),
    'low', 1, '2026-01-15 15:30:00'
  )
ON DUPLICATE KEY UPDATE
  `input_text` = VALUES(`input_text`),
  `candidate_titles` = VALUES(`candidate_titles`),
  `summary_short` = VALUES(`summary_short`),
  `summary_long` = VALUES(`summary_long`),
  `summary_points` = VALUES(`summary_points`),
  `keywords` = VALUES(`keywords`),
  `risk_level` = VALUES(`risk_level`),
  `status` = VALUES(`status`);

-- 社区帖子演示数据：用于社区页面数据库读取与互动测试
INSERT INTO `community_post` (
  `id`, `user_id`, `title`, `content`, `related_news_id`, `topic_id`, `tags`,
  `like_count`, `comment_count`, `favorite_count`, `view_count`, `heat_score`, `status`,
  `created_at`, `updated_at`
)
VALUES
  (
    1, 1, '大家平时会先看 AI 摘要还是直接读全文？',
    '最近新闻详情页已经可以跳转到 AI 标题摘要生成页，我试了一下，长新闻先看摘要确实更容易判断是否值得阅读全文。想和大家讨论一下：如果是科技、财经这类信息密度高的新闻，你们更希望摘要偏短、更客观，还是希望同时给出背景和后续影响？',
    1, 1, JSON_ARRAY('AI摘要', '阅读效率', '新闻详情'),
    8, 3, 3, 50, 96, 1, '2026-06-20 09:15:00', '2026-06-20 10:10:00'
  ),
  (
    2, 2, '低空经济新闻适合做事件脉络吗？',
    '低空经济相关报道往往涉及政策、产业园、无人机应用和安全规范。单篇新闻能提供一个角度，但如果能把同一话题下的报道按时间线串起来，应该更容易看清产业发展节奏。大家觉得事件脉络里最重要的是时间节点、来源新闻，还是节点摘要？',
    2, 2, JSON_ARRAY('低空经济', '事件脉络', '无人机'),
    12, 2, 4, 60, 118, 1, '2026-06-20 11:30:00', '2026-06-20 12:05:00'
  ),
  (
    3, 3, '新能源汽车和智能交通的数据怎么展示更直观？',
    '新能源汽车相关信息包含销量、充电设施、智能驾驶、城市交通等维度。如果后续个人中心能把用户阅读过的新能源新闻聚合成阅读脉络，可能可以帮助用户发现自己长期关注的话题。欢迎补充你们觉得适合可视化的字段。',
    3, 3, JSON_ARRAY('新能源汽车', '智能交通', '数据可视化'),
    10, 2, 2, 45, 105, 1, '2026-06-21 14:20:00', '2026-06-21 15:00:00'
  ),
  (
    4, 1, '社区讨论区可以增加哪些新闻互动入口？',
    '现在社区页已经有帖子列表、热搜话题和互动按钮。如果从新闻详情页进入社区讨论，最好能自动关联原新闻，并把标题、来源展示出来，这样讨论不会脱离新闻语境。这个帖子主要用来测试社区数据库数据展示和评论回复功能。',
    4, 1, JSON_ARRAY('社区互动', '关联新闻', '功能测试'),
    6, 2, 1, 30, 88, 1, '2026-06-22 08:45:00', '2026-06-22 09:30:00'
  ),
  (
    5, 2, '编辑视角：评论审核应该保留哪些状态？',
    '评论数据里已经有正常、折叠、待审核和删除等状态。为了演示后台审核能力，建议社区评论和新闻评论都保留状态字段，并在页面上区分正常展示和折叠展示。后续如果接入真实审核流程，也更容易扩展。',
    5, 1, JSON_ARRAY('评论审核', '后台管理', '数据状态'),
    5, 1, 1, 25, 76, 1, '2026-06-22 16:10:00', '2026-06-22 17:00:00'
  ),
  (
    6, 1, '待审核演示帖：社区内容审核流程测试',
    '这是一条用于管理后台待审核列表演示的帖子。普通社区列表不应展示，管理员后台或编辑后台可以读取到该状态，用于测试审核、筛选和后续管理流程。',
    6, 2, JSON_ARRAY('待审核', '管理后台', '演示数据'),
    0, 0, 0, 5, 20, 3, '2026-06-23 10:00:00', '2026-06-23 10:00:00'
  )
ON DUPLICATE KEY UPDATE
  `title` = VALUES(`title`),
  `content` = VALUES(`content`),
  `related_news_id` = VALUES(`related_news_id`),
  `topic_id` = VALUES(`topic_id`),
  `tags` = VALUES(`tags`),
  `like_count` = VALUES(`like_count`),
  `comment_count` = VALUES(`comment_count`),
  `favorite_count` = VALUES(`favorite_count`),
  `view_count` = VALUES(`view_count`),
  `heat_score` = VALUES(`heat_score`),
  `status` = VALUES(`status`),
  `updated_at` = VALUES(`updated_at`);

-- 社区评论演示数据：包含一级评论和回复评论
INSERT INTO `post_comment` (
  `id`, `post_id`, `user_id`, `parent_id`, `content`, `like_count`, `status`, `created_at`, `updated_at`
)
VALUES
  (1, 1, 2, NULL, '我更倾向先看短摘要，再决定是否阅读全文。尤其是长篇科技新闻，摘要能帮我快速抓重点。', 4, 1, '2026-06-20 09:35:00', '2026-06-20 09:35:00'),
  (2, 1, 3, NULL, '如果能同时给出“核心事实”和“可能影响”，会比单纯压缩正文更有价值。', 3, 1, '2026-06-20 09:50:00', '2026-06-20 09:50:00'),
  (3, 1, 1, 2, '同意，尤其是财经新闻，影响分析很重要，但也要标明是系统生成结果。', 2, 1, '2026-06-20 10:05:00', '2026-06-20 10:05:00'),
  (4, 2, 1, NULL, '低空经济很适合做时间线，政策和应用场景变化都比较明显。', 5, 1, '2026-06-20 11:45:00', '2026-06-20 11:45:00'),
  (5, 2, 3, 4, '可以把“政策发布、试点落地、产业园建设”作为节点类型，阅读会更清楚。', 3, 1, '2026-06-20 12:02:00', '2026-06-20 12:02:00'),
  (6, 3, 1, NULL, '个人中心的阅读脉络如果能按话题聚合，会比单纯列表更有帮助。', 4, 1, '2026-06-21 14:45:00', '2026-06-21 14:45:00'),
  (7, 3, 2, NULL, '新能源新闻还可以和时间线联动，看政策、企业、基础设施之间的关系。', 2, 1, '2026-06-21 14:58:00', '2026-06-21 14:58:00'),
  (8, 4, 3, NULL, '关联新闻很有必要，不然社区讨论容易变成泛泛聊天。', 3, 1, '2026-06-22 09:00:00', '2026-06-22 09:00:00'),
  (9, 4, 1, 8, '后续可以在详情页增加“参与讨论”入口，直接带上新闻 id。', 2, 1, '2026-06-22 09:18:00', '2026-06-22 09:18:00'),
  (10, 5, 3, NULL, '待审核和折叠状态最好在后台能筛选，这样演示逻辑更完整。', 1, 1, '2026-06-22 16:35:00', '2026-06-22 16:35:00')
ON DUPLICATE KEY UPDATE
  `content` = VALUES(`content`),
  `like_count` = VALUES(`like_count`),
  `status` = VALUES(`status`),
  `updated_at` = VALUES(`updated_at`);

-- 社区点赞、收藏、拉黑演示数据
INSERT INTO `user_like` (`user_id`, `target_id`, `target_type`, `created_at`)
VALUES
  (1, 2, 'community_post', '2026-06-20 12:10:00'),
  (1, 3, 'community_post', '2026-06-21 15:10:00'),
  (2, 1, 'community_post', '2026-06-20 09:40:00'),
  (3, 1, 'community_post', '2026-06-20 09:55:00'),
  (1, 1, 'post_comment', '2026-06-20 10:15:00'),
  (1, 4, 'post_comment', '2026-06-20 12:15:00'),
  (2, 6, 'post_comment', '2026-06-21 15:05:00'),
  (3, 8, 'post_comment', '2026-06-22 09:10:00')
ON DUPLICATE KEY UPDATE
  `created_at` = VALUES(`created_at`);

INSERT INTO `favorite` (`user_id`, `target_id`, `target_type`, `created_at`)
VALUES
  (1, 2, 'community_post', '2026-06-20 12:20:00'),
  (1, 3, 'community_post', '2026-06-21 15:20:00'),
  (2, 1, 'community_post', '2026-06-20 10:00:00'),
  (3, 2, 'community_post', '2026-06-20 12:25:00')
ON DUPLICATE KEY UPDATE
  `created_at` = VALUES(`created_at`);

INSERT INTO `user_block` (`user_id`, `blocked_user_id`, `created_at`)
VALUES
  (2, 3, '2026-06-22 18:00:00')
ON DUPLICATE KEY UPDATE
  `created_at` = VALUES(`created_at`);

-- 社区热搜与话题入口演示数据
INSERT INTO `hot_topic` (
  `id`, `title`, `target_type`, `target_id`, `heat_score`, `rank_no`, `tag`, `status`, `updated_at`, `created_at`
)
VALUES
  (4, 'AI 摘要如何改变新闻阅读', 'community_post', 1, 980, 4, '讨论', 1, '2026-06-20 10:10:00', '2026-06-20 10:10:00'),
  (5, '低空经济事件脉络', 'news_topic', 2, 940, 5, '时间线', 1, '2026-06-20 12:05:00', '2026-06-20 12:05:00'),
  (6, '新能源汽车与智能交通', 'news_topic', 3, 910, 6, '产业', 1, '2026-06-21 15:00:00', '2026-06-21 15:00:00'),
  (7, '社区互动功能测试', 'community_post', 4, 860, 7, '社区', 1, '2026-06-22 09:30:00', '2026-06-22 09:30:00'),
  (8, '评论审核与后台管理', 'community_post', 5, 820, 8, '管理', 1, '2026-06-22 17:00:00', '2026-06-22 17:00:00')
ON DUPLICATE KEY UPDATE
  `title` = VALUES(`title`),
  `target_type` = VALUES(`target_type`),
  `target_id` = VALUES(`target_id`),
  `heat_score` = VALUES(`heat_score`),
  `rank_no` = VALUES(`rank_no`),
  `tag` = VALUES(`tag`),
  `status` = VALUES(`status`),
  `updated_at` = VALUES(`updated_at`),
  `created_at` = VALUES(`created_at`);
