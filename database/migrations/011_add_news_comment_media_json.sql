-- 为新闻评论表新增富媒体字段
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'llm_news_system'
  AND TABLE_NAME = 'news_comment'
  AND COLUMN_NAME = 'media_json');

SET @sql = IF(@col_exists = 0,
  'ALTER TABLE `news_comment` ADD COLUMN `media_json` JSON NULL COMMENT ''评论媒体信息'' AFTER `content`',
  'SELECT ''Column media_json already exists'' AS info');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
