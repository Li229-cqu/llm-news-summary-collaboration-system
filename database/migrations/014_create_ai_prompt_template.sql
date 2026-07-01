-- M10: ai_prompt_template table for LLM prompt template management
-- Supports CRUD, enable/disable, and default-template-per-function_type logic

CREATE TABLE IF NOT EXISTS `ai_prompt_template` (
  `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`           VARCHAR(100) NOT NULL COMMENT '模板名称',
  `function_type`  VARCHAR(50) NOT NULL COMMENT '适用功能: title_generation/summary_generation/keyword_extraction/element_extraction/consistency_check/timeline_generation/ai_chat',
  `prompt_content` TEXT NOT NULL COMMENT '模板内容(Prompt 文本)',
  `version`        VARCHAR(32) NOT NULL DEFAULT 'v1' COMMENT '版本号',
  `status`         TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 1=启用, 0=停用',
  `is_default`     TINYINT NOT NULL DEFAULT 0 COMMENT '是否默认模板: 1=是, 0=否',
  `remark`         VARCHAR(255) DEFAULT '' COMMENT '备注说明',
  `created_at`     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_function_type` (`function_type`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
