SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS backup_record (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  backup_name VARCHAR(255) NOT NULL,
  backup_type VARCHAR(50) DEFAULT 'manual',
  file_path VARCHAR(500) DEFAULT '',
  file_size BIGINT DEFAULT 0,
  status VARCHAR(50) DEFAULT 'pending',
  message TEXT NULL,
  operator_id BIGINT UNSIGNED DEFAULT NULL,
  operator_name VARCHAR(100) DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  finished_at DATETIME DEFAULT NULL,
  PRIMARY KEY (id),
  KEY idx_backup_record_status_time (status, created_at),
  KEY idx_backup_record_type_time (backup_type, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
