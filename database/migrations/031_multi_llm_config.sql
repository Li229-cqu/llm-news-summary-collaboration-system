-- Migration: 031_multi_llm_config.sql
-- Phase 1: Multi-LLM provider configuration (DeepSeek + Zhipu dual model)
--
-- DeepSeek = 生成类任务（出题老师）：关键词、六要素、标题摘要、话题匹配
-- Zhipu   = 审核类任务（审题老师）：时间线、一致性检查、编辑建议

-- DeepSeek API 配置
INSERT IGNORE INTO `system_config` (`config_key`, `config_value`, `config_type`, `description`, `editable`) VALUES
('ai.deepseek.model', 'deepseek-chat', 'string', 'DeepSeek 模型名称', 1),
('ai.deepseek.timeout', '120', 'int', 'DeepSeek 请求超时(秒)', 1),
('ai.deepseek.base_url', 'https://api.deepseek.com/v1', 'string', 'DeepSeek API 地址', 1);

-- Zhipu API 配置（从旧 ai.* 配置迁移）

INSERT IGNORE INTO `system_config` (`config_key`, `config_value`, `config_type`, `description`, `editable`) VALUES
('ai.zhipu.model', 'glm-4-flash', 'string', 'Zhipu 模型名称', 1),
('ai.zhipu.timeout', '60', 'int', 'Zhipu 请求超时(秒)', 1),
('ai.zhipu.base_url', 'https://open.bigmodel.cn/api/paas/v4', 'string', 'Zhipu API 地址', 1);

-- 确保全局开关保持 enabled
UPDATE `system_config` SET `config_value` = 'true' WHERE `config_key` = 'ai.enable_real_llm';

-- 验证结果
SELECT config_key, config_value FROM system_config WHERE config_key LIKE 'ai.%' ORDER BY config_key;
