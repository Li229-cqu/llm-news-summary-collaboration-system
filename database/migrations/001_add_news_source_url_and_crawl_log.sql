USE llm_news_system;

SET @news_source_url_exists := (
  SELECT COUNT(1)
  FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'news'
    AND column_name = 'source_url'
);

SET @sql := IF(
  @news_source_url_exists = 0,
  'ALTER TABLE `news` ADD COLUMN `source_url` VARCHAR(500) DEFAULT NULL AFTER `source`',
  'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_exists := (
  SELECT COUNT(1)
  FROM information_schema.statistics
  WHERE table_schema = DATABASE()
    AND table_name = 'news'
    AND index_name = 'uk_news_source_url'
);

SET @sql := IF(
  @idx_exists = 0,
  'ALTER TABLE `news` ADD UNIQUE KEY `uk_news_source_url` (`source_url`)',
  'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS `crawl_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `source_name` VARCHAR(128) NOT NULL,
  `rss_url` VARCHAR(500) NOT NULL,
  `start_time` DATETIME NOT NULL,
  `end_time` DATETIME NOT NULL,
  `parsed_count` INT NOT NULL DEFAULT 0,
  `inserted_count` INT NOT NULL DEFAULT 0,
  `skipped_count` INT NOT NULL DEFAULT 0,
  `updated_count` INT NOT NULL DEFAULT 0,
  `failed_count` INT NOT NULL DEFAULT 0,
  `status` VARCHAR(32) NOT NULL,
  `error_message` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_crawl_log_source_name` (`source_name`),
  KEY `idx_crawl_log_status` (`status`),
  KEY `idx_crawl_log_start_time` (`start_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
