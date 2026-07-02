-- 029: 为 news_topic 增加自动/人工话题区分字段
-- 用途：保护人工创建的话题不被自动聚类流程覆盖

ALTER TABLE news_topic
ADD COLUMN IF NOT EXISTS source_type VARCHAR(16) NOT NULL DEFAULT 'manual'
COMMENT 'manual=人工话题, auto=自动聚类话题';

ALTER TABLE news_topic
ADD COLUMN IF NOT EXISTS auto_generated_at DATETIME NULL
COMMENT '自动聚类话题的生成时间';

-- 现有话题全部标记为人工创建
UPDATE news_topic SET source_type = 'manual' WHERE source_type = 'manual';
