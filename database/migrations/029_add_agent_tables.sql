-- News Editor Agent 系统数据库表
-- Migration: 029_add_agent_tables.sql
-- 说明：新增 agent_task 和 agent_step_log 两张表，用于记录 Agent 任务及每一步执行日志
-- 安全规则：不修改任何已有表结构，全部使用 IF NOT EXISTS

-- Agent 任务主表
CREATE TABLE IF NOT EXISTS `agent_task` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '执行用户ID',
  `news_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '关联的新闻ID（可选，支持自由文本）',
  `task_type` VARCHAR(64) NOT NULL DEFAULT 'news_editor' COMMENT '任务类型标识',
  `input_text` LONGTEXT NOT NULL COMMENT '原始输入文本',
  `cleaned_text` LONGTEXT COMMENT '清洗后文本（Step 1 输出）',
  `status` ENUM('pending','running','completed','failed','cancelled') NOT NULL DEFAULT 'pending' COMMENT '任务整体状态',
  `progress` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '完成百分比 0-100',
  `current_step` VARCHAR(64) DEFAULT NULL COMMENT '当前正在执行的步骤标识',
  `result_json` JSON DEFAULT NULL COMMENT '完整 Agent 执行结果聚合',
  `total_steps` TINYINT UNSIGNED NOT NULL DEFAULT 8 COMMENT '总步骤数',
  `completed_steps` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '已完成步骤数',
  `failed_step` VARCHAR(64) DEFAULT NULL COMMENT '失败步骤标识',
  `error_message` TEXT COMMENT '错误信息',
  `started_at` DATETIME DEFAULT NULL COMMENT '任务开始时间',
  `completed_at` DATETIME DEFAULT NULL COMMENT '任务完成时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_agent_task_user` (`user_id`),
  KEY `idx_agent_task_news` (`news_id`),
  KEY `idx_agent_task_status` (`status`),
  KEY `idx_agent_task_type` (`task_type`),
  KEY `idx_agent_task_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent 任务主表：记录一次完整的 Agent 执行任务';

-- Agent 步骤执行日志表
CREATE TABLE IF NOT EXISTS `agent_step_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `task_id` BIGINT UNSIGNED NOT NULL COMMENT '关联 agent_task.id',
  `step_order` TINYINT UNSIGNED NOT NULL COMMENT '步骤序号 1-8',
  `step_name` VARCHAR(64) NOT NULL COMMENT '步骤标识: clean/extract_keywords/extract_elements/generate/match_topic/judge_timeline/check/edit_suggestions',
  `step_label` VARCHAR(128) NOT NULL COMMENT '步骤中文名: 正文清洗/关键词提取/六要素识别/标题摘要生成/话题匹配/时间线适配/一致性检查/编辑建议生成',
  `status` ENUM('pending','running','completed','failed','skipped') NOT NULL DEFAULT 'pending' COMMENT '步骤执行状态',
  `input_data` JSON DEFAULT NULL COMMENT '步骤输入数据（裁剪后）',
  `output_data` JSON DEFAULT NULL COMMENT '步骤输出数据',
  `llm_provider` VARCHAR(32) DEFAULT NULL COMMENT 'LLM 提供商: deepseek/zhipu/local',
  `llm_model` VARCHAR(64) DEFAULT NULL COMMENT 'LLM 模型名称',
  `llm_request_tokens` INT UNSIGNED DEFAULT 0 COMMENT '请求 token 数量',
  `llm_response_tokens` INT UNSIGNED DEFAULT 0 COMMENT '响应 token 数量',
  `response_ms` INT UNSIGNED DEFAULT 0 COMMENT '步骤执行耗时（毫秒）',
  `error_message` TEXT COMMENT '错误信息',
  `retry_count` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '重试次数',
  `started_at` DATETIME DEFAULT NULL COMMENT '步骤开始时间',
  `completed_at` DATETIME DEFAULT NULL COMMENT '步骤完成时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_step_log_task` (`task_id`),
  KEY `idx_step_log_step_name` (`step_name`),
  KEY `idx_step_log_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent 步骤执行日志：记录每一步 Agent 执行过程的详细信息';
