ALTER TABLE ai_generate_record
  ADD COLUMN evidence_json LONGTEXT NULL COMMENT '证据链JSON数据',
  ADD COLUMN evidence_status TINYINT DEFAULT 0 COMMENT '证据状态(0=未评估,1=已评估,2=验证失败)',
  ADD COLUMN risk_level TINYINT DEFAULT 0 COMMENT '风险等级(0=低,1=中,2=高)',
  ADD COLUMN risk_details TEXT NULL COMMENT '风险详情描述',
  ADD COLUMN evidence_coverage DECIMAL(5,2) DEFAULT 0 COMMENT '证据覆盖率';