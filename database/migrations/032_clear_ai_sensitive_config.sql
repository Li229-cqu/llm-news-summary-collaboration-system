-- Clear AI-related sensitive values from system_config.
-- API keys must be configured only in ai-service/.env.

DELETE FROM `system_config`
WHERE LOWER(`config_key`) LIKE '%api_key%'
   OR REPLACE(REPLACE(REPLACE(LOWER(`config_key`), '_', ''), '-', ''), ' ', '') LIKE '%apikey%'
   OR LOWER(`config_key`) LIKE '%secret_key%'
   OR REPLACE(REPLACE(REPLACE(LOWER(`config_key`), '_', ''), '-', ''), ' ', '') LIKE '%secretkey%'
   OR LOWER(`config_key`) LIKE '%token%';

SELECT config_key, config_value
FROM system_config
WHERE LOWER(config_key) LIKE '%api_key%'
   OR REPLACE(REPLACE(REPLACE(LOWER(`config_key`), '_', ''), '-', ''), ' ', '') LIKE '%apikey%'
   OR LOWER(config_key) LIKE '%secret_key%'
   OR REPLACE(REPLACE(REPLACE(LOWER(`config_key`), '_', ''), '-', ''), ' ', '') LIKE '%secretkey%'
   OR LOWER(config_key) LIKE '%token%'
ORDER BY config_key;
