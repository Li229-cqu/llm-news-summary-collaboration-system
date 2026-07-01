-- M10: Add response_ms field to ai_generate_record for average latency calculation
ALTER TABLE `ai_generate_record` ADD COLUMN `response_ms` INT NOT NULL DEFAULT 0 COMMENT '响应时间(毫秒)' AFTER `ai_source`;
