USE llm_news_system;

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'hot_topic'
    AND COLUMN_NAME = 'status'
);

SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `hot_topic` ADD COLUMN `status` TINYINT NOT NULL DEFAULT 1 COMMENT ''状态：1正常，0禁用'' AFTER `tag`',
  'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
