SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'browse_history'
    AND COLUMN_NAME = 'target_type'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `browse_history` ADD COLUMN `target_type` VARCHAR(64) DEFAULT ''news'' COMMENT ''browse target type'' AFTER `news_id`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'browse_history'
    AND COLUMN_NAME = 'target_id'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `browse_history` ADD COLUMN `target_id` BIGINT UNSIGNED DEFAULT NULL COMMENT ''browse target id'' AFTER `target_type`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

ALTER TABLE `browse_history`
  MODIFY COLUMN `news_id` BIGINT UNSIGNED NOT NULL DEFAULT 0;

UPDATE `browse_history`
SET `target_type` = COALESCE(`target_type`, 'news'),
    `target_id` = COALESCE(`target_id`, NULLIF(`news_id`, 0))
WHERE `target_type` IS NULL OR `target_id` IS NULL;

SET @idx_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'browse_history'
    AND INDEX_NAME = 'idx_browse_history_target'
);
SET @sql := IF(
  @idx_exists = 0,
  'ALTER TABLE `browse_history` ADD INDEX `idx_browse_history_target` (`user_id`, `target_type`, `target_id`)',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
