-- M10: Sync AI configuration from .env file to database
-- Run this script after updating .env to sync AI config to database

-- Update AI service URL
UPDATE `system_config` SET `config_value` = 'http://127.0.0.1:8001' WHERE `config_key` = 'ai.service_url';

-- Update model name
UPDATE `system_config` SET `config_value` = 'glm-4-flash' WHERE `config_key` = 'ai.model_name';

-- Update API Key (copy from ai-service/.env EVIDENCE_LLM_API_KEY)
UPDATE `system_config` SET `config_value` = '1568a5f785a0424b92e89829d9301cc4.HED3mela1mK9KDeO' WHERE `config_key` = 'ai.api_key';

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
