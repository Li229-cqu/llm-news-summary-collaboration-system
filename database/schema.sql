-- =========================================================
-- LLM news summary collaboration system
-- MySQL schema
-- =========================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `user` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(64) NOT NULL,
  `password` VARCHAR(128) NOT NULL,
  `nickname` VARCHAR(64) DEFAULT '',
  `role` VARCHAR(32) NOT NULL DEFAULT 'user',
  `avatar` VARCHAR(500) DEFAULT '',
  `email` VARCHAR(128) DEFAULT NULL,
  `phone` VARCHAR(32) DEFAULT NULL,
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_username` (`username`),
  KEY `idx_user_role` (`role`),
  KEY `idx_user_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `news_category` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(64) NOT NULL,
  `code` VARCHAR(64) NOT NULL,
  `description` VARCHAR(255) DEFAULT '',
  `sort` INT NOT NULL DEFAULT 0,
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_news_category_code` (`code`),
  KEY `idx_news_category_status_sort` (`status`, `sort`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `news_topic` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `topic_name` VARCHAR(128) NOT NULL,
  `summary` TEXT,
  `keyword_list` JSON DEFAULT NULL,
  `heat_score` INT NOT NULL DEFAULT 0,
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_news_topic_status_heat` (`status`, `heat_score`),
  KEY `idx_news_topic_name` (`topic_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `news` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(255) NOT NULL,
  `summary` TEXT,
  `content` LONGTEXT,
  `cover_image` VARCHAR(500) DEFAULT '',
  `category_id` BIGINT UNSIGNED DEFAULT NULL,
  `topic_id` BIGINT UNSIGNED DEFAULT NULL,
  `source` VARCHAR(128) DEFAULT '',
  `editor` VARCHAR(128) DEFAULT NULL,
  `publish_time` DATETIME DEFAULT NULL,
  `source_url` VARCHAR(500) DEFAULT NULL,
  `view_count` INT NOT NULL DEFAULT 0,
  `like_count` INT NOT NULL DEFAULT 0,
  `comment_count` INT NOT NULL DEFAULT 0,
  `favorite_count` INT NOT NULL DEFAULT 0,
  `tags` JSON DEFAULT NULL,
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_news_source_url` (`source_url`),
  KEY `idx_news_category` (`category_id`),
  KEY `idx_news_topic` (`topic_id`),
  KEY `idx_news_status_publish` (`status`, `publish_time`),
  KEY `idx_news_hot` (`view_count`, `like_count`, `comment_count`),
  KEY `idx_news_title` (`title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `news_comment` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `news_id` BIGINT UNSIGNED NOT NULL,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `parent_id` BIGINT UNSIGNED DEFAULT NULL,
  `content` TEXT NOT NULL,
  `media_json` JSON DEFAULT NULL,
  `like_count` INT NOT NULL DEFAULT 0,
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_news_comment_news` (`news_id`),
  KEY `idx_news_comment_user` (`user_id`),
  KEY `idx_news_comment_parent` (`parent_id`),
  KEY `idx_news_comment_status_time` (`status`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `user_like` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `target_type` VARCHAR(64) NOT NULL,
  `target_id` BIGINT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_like_target` (`user_id`, `target_type`, `target_id`),
  KEY `idx_user_like_target` (`target_type`, `target_id`),
  KEY `idx_user_like_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `favorite` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `target_type` VARCHAR(64) NOT NULL,
  `target_id` BIGINT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_favorite_target` (`user_id`, `target_type`, `target_id`),
  KEY `idx_favorite_target` (`target_type`, `target_id`),
  KEY `idx_favorite_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `browse_history` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `news_id` BIGINT UNSIGNED NOT NULL DEFAULT 0,
  `target_type` VARCHAR(64) DEFAULT 'news',
  `target_id` BIGINT UNSIGNED DEFAULT NULL,
  `browse_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_browse_history_user_time` (`user_id`, `browse_time`),
  KEY `idx_browse_history_news` (`news_id`),
  KEY `idx_browse_history_target` (`user_id`, `target_type`, `target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `ai_generate_record` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED DEFAULT NULL,
  `source` VARCHAR(32) NOT NULL DEFAULT 'manual',
  `source_news_id` BIGINT UNSIGNED DEFAULT NULL,
  `source_title` VARCHAR(255) DEFAULT '',
  `input_text` LONGTEXT NOT NULL,
  `title_count` INT NOT NULL DEFAULT 3,
  `summary_type` VARCHAR(32) NOT NULL DEFAULT 'generate',
  `summary_style` VARCHAR(64) DEFAULT '',
  `title_style` VARCHAR(64) DEFAULT '',
  `summary_length` VARCHAR(32) DEFAULT 'both',
  `candidate_titles` JSON DEFAULT NULL,
  `summary_short` TEXT,
  `summary_long` TEXT,
  `summary_points` JSON DEFAULT NULL,
  `keywords` JSON DEFAULT NULL,
  `news_elements` JSON DEFAULT NULL,
  `risk_level` VARCHAR(32) DEFAULT 'low',
  `risk_details` TEXT NULL,
  `check_result` JSON DEFAULT NULL,
  `ai_source` VARCHAR(16) DEFAULT 'mock',
  `response_ms` INT NOT NULL DEFAULT 0,
  `evidence_json` LONGTEXT NULL,
  `evidence_status` TINYINT DEFAULT 0,
  `evidence_coverage` DECIMAL(5,2) DEFAULT 0,
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_ai_record_user_time` (`user_id`, `created_at`),
  KEY `idx_ai_record_source_news` (`source_news_id`),
  KEY `idx_ai_record_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `upload_file` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED DEFAULT NULL,
  `file_name` VARCHAR(255) NOT NULL,
  `file_path` VARCHAR(500) NOT NULL,
  `file_url` VARCHAR(500) DEFAULT '',
  `file_type` VARCHAR(64) DEFAULT '',
  `mime_type` VARCHAR(128) DEFAULT '',
  `file_size` BIGINT DEFAULT 0,
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_upload_user` (`user_id`),
  KEY `idx_upload_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `community_post` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `content` LONGTEXT,
  `related_news_id` BIGINT UNSIGNED DEFAULT NULL,
  `topic_id` BIGINT UNSIGNED DEFAULT NULL,
  `tags` JSON DEFAULT NULL,
  `images` JSON DEFAULT NULL COMMENT '帖子图片URL列表',
  `like_count` INT NOT NULL DEFAULT 0,
  `comment_count` INT NOT NULL DEFAULT 0,
  `favorite_count` INT NOT NULL DEFAULT 0,
  `view_count` INT NOT NULL DEFAULT 0,
  `heat_score` INT NOT NULL DEFAULT 0,
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_community_post_user` (`user_id`),
  KEY `idx_community_post_news` (`related_news_id`),
  KEY `idx_community_post_topic` (`topic_id`),
  KEY `idx_community_post_status_heat` (`status`, `heat_score`),
  KEY `idx_community_post_time` (`created_at`),
  KEY `idx_community_post_view_count` (`view_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `post_comment` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `post_id` BIGINT UNSIGNED NOT NULL,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `parent_id` BIGINT UNSIGNED DEFAULT NULL,
  `content` TEXT NOT NULL,
  `media_json` LONGTEXT NULL,
  `like_count` INT NOT NULL DEFAULT 0,
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_post_comment_post` (`post_id`),
  KEY `idx_post_comment_user` (`user_id`),
  KEY `idx_post_comment_parent` (`parent_id`),
  KEY `idx_post_comment_status_time` (`status`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `user_block` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `blocked_user_id` BIGINT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_block` (`user_id`, `blocked_user_id`),
  KEY `idx_user_block_user` (`user_id`),
  KEY `idx_user_block_blocked` (`blocked_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `hot_topic` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(255) NOT NULL,
  `target_type` VARCHAR(64) DEFAULT 'news',
  `target_id` BIGINT UNSIGNED DEFAULT NULL,
  `heat_score` INT NOT NULL DEFAULT 0,
  `rank_no` INT NOT NULL DEFAULT 0,
  `tag` VARCHAR(64) DEFAULT '',
  `status` TINYINT NOT NULL DEFAULT 1,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_hot_topic_rank` (`rank_no`, `heat_score`),
  KEY `idx_hot_topic_target` (`target_type`, `target_id`),
  KEY `idx_hot_topic_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `event_timeline` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `topic_id` BIGINT UNSIGNED NOT NULL,
  `timeline_json` JSON NOT NULL,
  `source_news_ids` JSON DEFAULT NULL,
  `metadata_json` TEXT DEFAULT NULL,
  `relationships_json` TEXT DEFAULT NULL,
  `schema_version` VARCHAR(20) DEFAULT '1.0',
  `generate_status` VARCHAR(32) NOT NULL DEFAULT 'success',
  `error_message` TEXT,
  `generated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_event_timeline_topic` (`topic_id`),
  KEY `idx_event_timeline_status` (`generate_status`),
  KEY `idx_event_timeline_time` (`generated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `crawl_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `source_name` VARCHAR(128) DEFAULT '',
  `rss_url` VARCHAR(500) DEFAULT '',
  `start_time` DATETIME DEFAULT NULL,
  `end_time` DATETIME DEFAULT NULL,
  `parsed_count` INT NOT NULL DEFAULT 0,
  `inserted_count` INT NOT NULL DEFAULT 0,
  `skipped_count` INT NOT NULL DEFAULT 0,
  `updated_count` INT NOT NULL DEFAULT 0,
  `failed_count` INT NOT NULL DEFAULT 0,
  `status` VARCHAR(32) NOT NULL DEFAULT 'success',
  `error_message` TEXT,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_crawl_log_source` (`source_name`),
  KEY `idx_crawl_log_status` (`status`),
  KEY `idx_crawl_log_time` (`start_time`, `end_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `user_category_subscription` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `category_id` BIGINT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_category_subscription` (`user_id`, `category_id`),
  KEY `idx_user_category_subscription_user` (`user_id`),
  KEY `idx_user_category_subscription_category` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- 绀惧尯 AI 浼氳瘽琛?
-- =========================================================
CREATE TABLE IF NOT EXISTS `community_ai_session` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `summary` VARCHAR(500) DEFAULT NULL,
  `source_type` VARCHAR(50) DEFAULT NULL,
  `source_post_id` BIGINT UNSIGNED DEFAULT NULL,
  `source_news_id` BIGINT UNSIGNED DEFAULT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'active',
  `last_message_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_community_ai_session_user_id` (`user_id`),
  KEY `idx_community_ai_session_last_message_at` (`last_message_at`),
  KEY `idx_community_ai_session_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- 绀惧尯 AI 娑堟伅琛?
-- =========================================================
CREATE TABLE IF NOT EXISTS `community_ai_message` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `session_id` BIGINT UNSIGNED NOT NULL,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `role` VARCHAR(20) NOT NULL,
  `content` TEXT NOT NULL,
  `request_payload` JSON DEFAULT NULL,
  `response_payload` JSON DEFAULT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'success',
  `error_message` TEXT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_community_ai_message_session_id` (`session_id`),
  KEY `idx_community_ai_message_user_id` (`user_id`),
  KEY `idx_community_ai_message_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `profile_weekly_report_cache` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `range_days` INT NOT NULL DEFAULT 7,
  `report_date` DATE NOT NULL,
  `input_hash` VARCHAR(64) NOT NULL,
  `ai_summary` TEXT,
  `ai_insights` JSON DEFAULT NULL,
  `ai_suggestions` JSON DEFAULT NULL,
  `ai_source` VARCHAR(32) NOT NULL DEFAULT 'llm',
  `quality_score` DECIMAL(3,2) NOT NULL DEFAULT 0.00,
  `page_analyses_overview` TEXT NULL,
  `page_analyses_trajectory` TEXT NULL,
  `page_analyses_conclusion` TEXT NULL,
  `reading_style` TEXT NULL,
  `closing` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_report` (`user_id`, `range_days`, `report_date`, `input_hash`),
  KEY `idx_user_date` (`user_id`, `report_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `system_config` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `config_key` VARCHAR(100) NOT NULL,
  `config_value` TEXT,
  `config_type` VARCHAR(32) NOT NULL DEFAULT 'string',
  `description` VARCHAR(255) DEFAULT '',
  `editable` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
