-- 029: 为 news_topic 增加自动/人工话题区分字段
-- 用途：保护人工创建的话题不被自动聚类流程覆盖

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'llm_news_system'
    AND TABLE_NAME = 'news_topic'
    AND COLUMN_NAME = 'source_type'
);

SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE news_topic ADD COLUMN source_type VARCHAR(16) NOT NULL DEFAULT ''manual'' COMMENT ''manual=人工话题, auto=自动聚类话题''',
  'SELECT ''Column source_type already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'llm_news_system'
    AND TABLE_NAME = 'news_topic'
    AND COLUMN_NAME = 'auto_generated_at'
);

SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE news_topic ADD COLUMN auto_generated_at DATETIME NULL COMMENT ''自动聚类话题的生成时间''',
  'SELECT ''Column auto_generated_at already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 现有话题全部标记为人工创建
UPDATE news_topic SET source_type = 'manual' WHERE source_type IS NULL OR source_type = '';
