SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ai_generate_record'
    AND COLUMN_NAME = 'response_ms'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `ai_generate_record` ADD COLUMN `response_ms` INT NOT NULL DEFAULT 0 COMMENT ''response time in milliseconds'' AFTER `ai_source`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
