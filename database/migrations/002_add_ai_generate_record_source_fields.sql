-- DB7: 为 AI 生成记录补充来源字段，便于个人中心展示真实生成历史
USE llm_news_system;

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ai_generate_record'
    AND COLUMN_NAME = 'source'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `ai_generate_record` ADD COLUMN `source` VARCHAR(16) NOT NULL DEFAULT ''manual'' COMMENT ''来源类型：manual、news''',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ai_generate_record'
    AND COLUMN_NAME = 'source_title'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `ai_generate_record` ADD COLUMN `source_title` VARCHAR(255) NOT NULL DEFAULT '''' COMMENT ''来源标题''',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ai_generate_record'
    AND INDEX_NAME = 'idx_ai_generate_record_source'
);
SET @sql := IF(
  @idx_exists = 0,
  'CREATE INDEX `idx_ai_generate_record_source` ON `ai_generate_record` (`source`)',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ai_generate_record'
    AND INDEX_NAME = 'idx_ai_generate_record_source_title'
);
SET @sql := IF(
  @idx_exists = 0,
  'CREATE INDEX `idx_ai_generate_record_source_title` ON `ai_generate_record` (`source_title`)',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
