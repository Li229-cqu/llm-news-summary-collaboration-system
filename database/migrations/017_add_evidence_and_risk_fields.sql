SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ai_generate_record'
    AND COLUMN_NAME = 'evidence_json'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `ai_generate_record` ADD COLUMN `evidence_json` LONGTEXT NULL COMMENT ''evidence chain JSON''',
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
    AND COLUMN_NAME = 'evidence_status'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `ai_generate_record` ADD COLUMN `evidence_status` TINYINT DEFAULT 0 COMMENT ''evidence status'' AFTER `evidence_json`',
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
    AND COLUMN_NAME = 'risk_details'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `ai_generate_record` ADD COLUMN `risk_details` TEXT NULL COMMENT ''risk details'' AFTER `risk_level`',
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
    AND COLUMN_NAME = 'evidence_coverage'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `ai_generate_record` ADD COLUMN `evidence_coverage` DECIMAL(5,2) DEFAULT 0 COMMENT ''evidence coverage'' AFTER `risk_details`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
