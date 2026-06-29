USE llm_news_system;

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'hot_topic'
    AND COLUMN_NAME = 'is_pinned'
);

SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `hot_topic` ADD COLUMN `is_pinned` TINYINT NOT NULL DEFAULT 0 COMMENT ''是否置顶：1置顶，0不置顶'' AFTER `status`',
  'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
