SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'community_post'
    AND COLUMN_NAME = 'view_count'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `community_post` ADD COLUMN `view_count` INT NOT NULL DEFAULT 0 COMMENT ''view count'' AFTER `favorite_count`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'community_post'
    AND INDEX_NAME = 'idx_community_post_view_count'
);
SET @sql := IF(
  @idx_exists = 0,
  'ALTER TABLE `community_post` ADD INDEX `idx_community_post_view_count` (`view_count`)',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
