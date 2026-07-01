-- 017: 个人页阅读报告缓存表
-- 缓存 AI 生成的周报文案，避免每次请求都调用 ai-service
-- input_hash 基于用户近 7 天行为数据的聚合统计计算，数据变化时自动失效

CREATE TABLE IF NOT EXISTS `profile_weekly_report_cache` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `range_days` INT NOT NULL DEFAULT 7,
  `report_date` DATE NOT NULL COMMENT '报告日期（CURDATE）',
  `input_hash` VARCHAR(64) NOT NULL COMMENT '基于结构化数据的 hash',
  `ai_summary` TEXT COMMENT 'AI 生成的总结文案',
  `ai_insights` JSON DEFAULT NULL COMMENT 'AI 洞察列表',
  `ai_suggestions` JSON DEFAULT NULL COMMENT 'AI 建议列表',
  `ai_source` VARCHAR(32) NOT NULL DEFAULT 'llm' COMMENT 'llm / fallback',
  `quality_score` DECIMAL(3,2) NOT NULL DEFAULT 0.00,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_report` (`user_id`, `range_days`, `report_date`, `input_hash`),
  KEY `idx_user_date` (`user_id`, `report_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
