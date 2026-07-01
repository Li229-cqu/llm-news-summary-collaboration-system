SET NAMES utf8mb4;

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'profile_weekly_report_cache'
    AND COLUMN_NAME = 'page_analyses_overview'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `profile_weekly_report_cache` ADD COLUMN `page_analyses_overview` TEXT NULL COMMENT ''Overview page analysis'' AFTER `quality_score`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'profile_weekly_report_cache'
    AND COLUMN_NAME = 'page_analyses_trajectory'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `profile_weekly_report_cache` ADD COLUMN `page_analyses_trajectory` TEXT NULL COMMENT ''Trajectory page analysis'' AFTER `page_analyses_overview`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'profile_weekly_report_cache'
    AND COLUMN_NAME = 'page_analyses_conclusion'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `profile_weekly_report_cache` ADD COLUMN `page_analyses_conclusion` TEXT NULL COMMENT ''Conclusion page analysis'' AFTER `page_analyses_trajectory`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'profile_weekly_report_cache'
    AND COLUMN_NAME = 'reading_style'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `profile_weekly_report_cache` ADD COLUMN `reading_style` TEXT NULL COMMENT ''Reading style text'' AFTER `page_analyses_conclusion`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'profile_weekly_report_cache'
    AND COLUMN_NAME = 'closing'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `profile_weekly_report_cache` ADD COLUMN `closing` TEXT NULL COMMENT ''Closing text'' AFTER `reading_style`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
