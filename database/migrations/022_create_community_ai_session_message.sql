SET NAMES utf8mb4;

-- =========================================================
-- 社区 AI 会话表
-- =========================================================
CREATE TABLE IF NOT EXISTS `community_ai_session` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `title` VARCHAR(255) NOT NULL COMMENT '会话标题',
  `summary` VARCHAR(500) DEFAULT NULL COMMENT '会话摘要',
  `source_type` VARCHAR(50) DEFAULT NULL COMMENT '来源类型：post/news',
  `source_post_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '来源帖子ID',
  `source_news_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '来源新闻ID',
  `status` VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态：active/deleted',
  `last_message_at` DATETIME DEFAULT NULL COMMENT '最后消息时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_community_ai_session_user_id` (`user_id`),
  KEY `idx_community_ai_session_last_message_at` (`last_message_at`),
  KEY `idx_community_ai_session_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- 社区 AI 消息表
-- =========================================================
CREATE TABLE IF NOT EXISTS `community_ai_message` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `session_id` BIGINT UNSIGNED NOT NULL COMMENT '会话ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `role` VARCHAR(20) NOT NULL COMMENT '角色：user/assistant/system',
  `content` TEXT NOT NULL COMMENT '消息内容',
  `request_payload` JSON DEFAULT NULL COMMENT '请求负载',
  `response_payload` JSON DEFAULT NULL COMMENT '响应负载',
  `status` VARCHAR(20) NOT NULL DEFAULT 'success' COMMENT '状态：success/failed',
  `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_community_ai_message_session_id` (`session_id`),
  KEY `idx_community_ai_message_user_id` (`user_id`),
  KEY `idx_community_ai_message_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
