-- =========================================================
-- 《基于大语言模型的智能新闻摘要与协同互动系统》
-- MySQL 8.0 数据库表结构（修正版）
-- =========================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `user` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` VARCHAR(64) NOT NULL COMMENT '用户名',
  `password` VARCHAR(128) NOT NULL COMMENT '密码',
  `nickname` VARCHAR(64) DEFAULT '' COMMENT '昵称',
  `role` VARCHAR(32) NOT NULL DEFAULT 'user' COMMENT '角色',
  `avatar` VARCHAR(500) DEFAULT '' COMMENT '头像URL',
  `email` VARCHAR(128) DEFAULT NULL COMMENT '邮箱',
  `phone` VARCHAR(32) DEFAULT NULL COMMENT '手机号',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态',
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
  `editor` VARCHAR(128) DEFAULT NULL COMMENT '新闻编辑',
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
  `media_json` JSON DEFAULT NULL COMMENT '评论媒体信息',
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
  `news_id` BIGINT UNSIGNED NOT NULL,
  `browse_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_browse_history_user_time` (`user_id`, `browse_time`),
  KEY `idx_browse_history_news` (`news_id`)
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
  `check_result` JSON DEFAULT NULL,
  `ai_source` VARCHAR(16) DEFAULT 'mock' COMMENT 'AI来源：mock（模拟）、llm（真实AI）',
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
  KEY `idx_community_post_time` (`created_at`)
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

SET FOREIGN_KEY_CHECKS = 1;
