USE llm_news_system;

SET @column_exists := (
  SELECT COUNT(*)
  FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'post_comment'
    AND column_name = 'media_json'
);

SET @sql := IF(
  @column_exists = 0,
  'ALTER TABLE post_comment ADD COLUMN media_json LONGTEXT NULL AFTER content',
  'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
