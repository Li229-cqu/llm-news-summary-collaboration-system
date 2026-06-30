-- 为 AI 生成记录表新增 ai_source 字段，区分真实 AI 和 Mock 演示
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'llm_news_system'
  AND TABLE_NAME = 'ai_generate_record'
  AND COLUMN_NAME = 'ai_source');

SET @sql = IF(@col_exists = 0,
  'ALTER TABLE `ai_generate_record` ADD COLUMN `ai_source` VARCHAR(16) DEFAULT ''mock'' COMMENT ''AI来源：mock（模拟）、llm（真实AI）'' AFTER `check_result`',
  'SELECT ''Column ai_source already exists'' AS info');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
