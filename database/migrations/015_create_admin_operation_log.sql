SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS admin_operation_log (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  operator_id BIGINT UNSIGNED DEFAULT NULL,
  operator_name VARCHAR(100) DEFAULT '',
  operator_role VARCHAR(50) DEFAULT '',
  module VARCHAR(100) DEFAULT '',
  action VARCHAR(100) DEFAULT '',
  target_type VARCHAR(100) DEFAULT '',
  target_id VARCHAR(100) DEFAULT '',
  description VARCHAR(500) DEFAULT '',
  ip_address VARCHAR(100) DEFAULT '',
  user_agent VARCHAR(500) DEFAULT '',
  result VARCHAR(50) DEFAULT 'success',
  error_message TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_admin_operation_log_operator (operator_id, created_at),
  KEY idx_admin_operation_log_module_action (module, action),
  KEY idx_admin_operation_log_result_time (result, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
