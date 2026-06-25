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
