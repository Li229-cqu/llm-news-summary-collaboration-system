-- M10: Sync non-sensitive AI configuration defaults to database.
-- API keys must stay in ai-service/.env and are not copied to system_config.

-- Update AI service URL
UPDATE `system_config` SET `config_value` = 'http://127.0.0.1:8001' WHERE `config_key` = 'ai.service_url';

-- Update model name
UPDATE `system_config` SET `config_value` = 'glm-4-flash' WHERE `config_key` = 'ai.model_name';

-- Clear historical API key values if this legacy key exists.
DELETE FROM `system_config`
WHERE REPLACE(REPLACE(REPLACE(LOWER(`config_key`), '_', ''), '-', ''), ' ', '') LIKE '%apikey%'
   OR REPLACE(REPLACE(REPLACE(LOWER(`config_key`), '_', ''), '-', ''), ' ', '') LIKE '%secretkey%'
   OR LOWER(`config_key`) LIKE '%token%';

-- Update timeout (copy from ai-service/.env LLM_TIMEOUT)
UPDATE `system_config` SET `config_value` = '45' WHERE `config_key` = 'ai.timeout';

-- Update max input length
UPDATE `system_config` SET `config_value` = '8000' WHERE `config_key` = 'ai.max_input_length';

-- Update enable_real_llm (copy from ai-service/.env LLM_ENABLED)
UPDATE `system_config` SET `config_value` = 'false' WHERE `config_key` = 'ai.enable_real_llm';

-- Update enable_fallback
UPDATE `system_config` SET `config_value` = 'true' WHERE `config_key` = 'ai.enable_fallback';

-- Update risk thresholds
UPDATE `system_config` SET `config_value` = '0.3' WHERE `config_key` = 'ai.risk.threshold.low';
UPDATE `system_config` SET `config_value` = '0.7' WHERE `config_key` = 'ai.risk.threshold.medium';

SELECT 'AI configuration synced successfully' AS message;
