-- Migration: 030_enable_real_llm.sql
-- Phase 4: Enable real LLM calls in agent pipeline
--
-- Legacy migration retained for ordering.
-- API keys must stay in ai-service/.env and are not written to system_config.

-- 启用真实 LLM 调用
UPDATE `system_config` SET `config_value` = 'true' WHERE `config_key` = 'ai.enable_real_llm';

-- Clear historical API key values if present.
DELETE FROM `system_config`
WHERE REPLACE(REPLACE(REPLACE(LOWER(`config_key`), '_', ''), '-', ''), ' ', '') LIKE '%apikey%'
   OR REPLACE(REPLACE(REPLACE(LOWER(`config_key`), '_', ''), '-', ''), ' ', '') LIKE '%secretkey%'
   OR LOWER(`config_key`) LIKE '%token%';

-- 确保 model_name 正确
UPDATE `system_config`
SET `config_value` = 'glm-4-flash'
WHERE `config_key` = 'ai.model_name'
AND (`config_value` IS NULL OR `config_value` = '');

-- 验证结果
SELECT config_key, config_value FROM system_config WHERE config_key LIKE 'ai.%' ORDER BY config_key;
