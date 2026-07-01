CREATE TABLE IF NOT EXISTS `system_config` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `config_key` VARCHAR(100) NOT NULL COMMENT 'config key',
  `config_value` TEXT COMMENT 'config value',
  `config_type` VARCHAR(32) NOT NULL DEFAULT 'string' COMMENT 'string/int/float/boolean/json',
  `description` VARCHAR(255) DEFAULT '' COMMENT 'description',
  `editable` TINYINT NOT NULL DEFAULT 1 COMMENT 'editable flag',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `system_config` (`config_key`, `config_value`, `config_type`, `description`, `editable`) VALUES
('site_name', '基于大语言模型的智能新闻摘要与协同互动系统', 'string', '站点名称', 1),
('site_description', '基于大语言模型的智能新闻摘要与协同互动系统', 'string', '站点描述', 1),
('max_upload_size', '10', 'int', '最大上传大小(MB)', 1),
('default_page_size', '10', 'int', '默认每页条数', 1),
('auto_approve_enabled', 'false', 'boolean', '是否启用自动审核', 1),
('ai.service_url', 'http://127.0.0.1:8001', 'string', 'AI 服务地址', 1),
('ai.model_name', 'glm-4-flash', 'string', '模型名称', 1),
('ai.api_key', '', 'string', 'AI API 密钥', 1),
('ai.timeout', '60', 'int', 'AI 请求超时(秒)', 1),
('ai.max_input_length', '8000', 'int', '最大输入长度', 1),
('ai.enable_real_llm', 'false', 'boolean', '是否启用真实 LLM 调用', 1),
('ai.enable_fallback', 'true', 'boolean', '真实 LLM 失败时是否启用规则兜底', 1),
('ai.enable_cache', 'false', 'boolean', '是否启用 AI 结果缓存', 0),
('ai.risk.threshold.low', '0.3', 'float', 'AI 生成低风险阈值', 1),
('ai.risk.threshold.medium', '0.7', 'float', 'AI 生成中风险阈值', 1),
('ai.sensitive_words', '[]', 'json', '敏感词列表(JSON 数组)', 1),
('ai.risk_rules', '[]', 'json', '风险规则配置(JSON)', 1),
('ai.fallback_strategy', '{}', 'json', '降级策略配置(JSON)', 1),
('timeline.enable_cache', 'false', 'boolean', 'Timeline 缓存启用', 1);
