CREATE TABLE IF NOT EXISTS event (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '事件ID',
    title VARCHAR(500) NOT NULL COMMENT '事件标题',
    description TEXT NULL COMMENT '事件描述',
    keywords VARCHAR(500) NULL COMMENT '关键词（逗号分隔）',
    status TINYINT DEFAULT 1 COMMENT '状态(0=草稿,1=已发布,2=已归档)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_event_title (title),
    INDEX idx_event_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='事件表';

CREATE TABLE IF NOT EXISTS event_news_relation (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '关联ID',
    event_id INT NOT NULL COMMENT '事件ID',
    news_id INT NOT NULL COMMENT '新闻ID',
    similarity DECIMAL(5,4) DEFAULT 0 COMMENT '相似度',
    source_priority TINYINT DEFAULT 0 COMMENT '来源优先级',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_event_news (event_id, news_id),
    INDEX idx_event_id (event_id),
    INDEX idx_news_id (news_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='事件新闻关联表';

CREATE TABLE IF NOT EXISTS event_conflict (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '冲突ID',
    event_id INT NOT NULL COMMENT '事件ID',
    conflict_type VARCHAR(50) NOT NULL COMMENT '冲突类型(numeric/entity/description)',
    field_name VARCHAR(100) NULL COMMENT '冲突字段名',
    news1_id INT NOT NULL COMMENT '新闻1ID',
    news1_value TEXT NULL COMMENT '新闻1的值',
    news2_id INT NOT NULL COMMENT '新闻2ID',
    news2_value TEXT NULL COMMENT '新闻2的值',
    similarity DECIMAL(5,4) DEFAULT 0 COMMENT '语义相似度',
    status TINYINT DEFAULT 0 COMMENT '状态(0=待审核,1=已确认,2=已排除)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_event_conflict (event_id),
    INDEX idx_conflict_type (conflict_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='事件冲突表';