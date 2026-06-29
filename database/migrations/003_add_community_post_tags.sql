USE llm_news_system;

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'community_post'
    AND COLUMN_NAME = 'tags'
);

SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `community_post` ADD COLUMN `tags` JSON NULL COMMENT ''社区帖子标签'' AFTER `updated_at`',
  'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
