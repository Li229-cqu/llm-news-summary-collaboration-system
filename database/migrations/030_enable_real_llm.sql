-- Migration: 030_enable_real_llm.sql
-- Phase 4: Enable real LLM calls in agent pipeline
--
-- 将 ai.enable_real_llm 设为 true，并确保 API Key 已配置。
-- 如果 ai.api_key 为空，从 migration 026 的默认值回填（Zhipu GLM key）。

-- 启用真实 LLM 调用
UPDATE `system_config` SET `config_value` = 'true' WHERE `config_key` = 'ai.enable_real_llm';

-- 如果 API Key 为空，使用 Zhipu GLM 默认 key（来自 migration 026）
UPDATE `system_config`
SET `config_value` = '1568a5f785a0424b92e89829d9301cc4.HED3mela1mK9KDeO'
WHERE `config_key` = 'ai.api_key'
AND (`config_value` IS NULL OR `config_value` = '' OR `config_value` = 'your_api_key');

-- 确保 model_name 正确
UPDATE `system_config`
SET `config_value` = 'glm-4-flash'
WHERE `config_key` = 'ai.model_name'
AND (`config_value` IS NULL OR `config_value` = '');

-- 验证结果
SELECT config_key, config_value FROM system_config WHERE config_key LIKE 'ai.%' ORDER BY config_key;
