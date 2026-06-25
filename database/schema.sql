-- 基于大语言模型的智能新闻摘要与协同互动系统
-- DB1：项目基础表结构
-- 说明：当前仅创建表结构，不插入 seed 数据，不建立外键，便于后续 mock 数据导入与开发联调。

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `event_timeline`;
DROP TABLE IF EXISTS `hot_topic`;
DROP TABLE IF EXISTS `user_block`;
DROP TABLE IF EXISTS `post_comment`;
DROP TABLE IF EXISTS `community_post`;
DROP TABLE IF EXISTS `upload_file`;
DROP TABLE IF EXISTS `ai_generate_record`;
DROP TABLE IF EXISTS `browse_history`;
DROP TABLE IF EXISTS `favorite`;
DROP TABLE IF EXISTS `user_like`;
DROP TABLE IF EXISTS `news_comment`;
DROP TABLE IF EXISTS `news`;
DROP TABLE IF EXISTS `news_topic`;
DROP TABLE IF EXISTS `news_category`;
DROP TABLE IF EXISTS `user`;

CREATE TABLE `user` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` VARCHAR(64) NOT NULL COMMENT '用户名',
  `password` VARCHAR(255) NOT NULL COMMENT '密码（当前阶段可为 mock 值，后续替换为加密密码）',
  `nickname` VARCHAR(64) NOT NULL COMMENT '昵称',
  `avatar` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '头像地址',
  `role` VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '角色：user/editor/admin',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1正常，0禁用',
  `bio` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '个人简介',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_username` (`username`),
  KEY `idx_user_role` (`role`),
  KEY `idx_user_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

CREATE TABLE `news_category` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `name` VARCHAR(64) NOT NULL COMMENT '分类名称',
  `code` VARCHAR(64) NOT NULL COMMENT '分类编码',
  `sort` INT NOT NULL DEFAULT 0 COMMENT '排序',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1正常，0禁用',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_news_category_code` (`code`),
  KEY `idx_news_category_status_sort` (`status`, `sort`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻分类表';

CREATE TABLE `news_topic` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '话题ID',
  `topic_name` VARCHAR(128) NOT NULL COMMENT '话题名称',
  `keyword_list` JSON NULL COMMENT '关键词列表',
  `heat_score` INT NOT NULL DEFAULT 0 COMMENT '热度值',
  `summary` TEXT NULL COMMENT '话题简介',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1正常，0禁用',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_news_topic_status_heat` (`status`, `heat_score`),
  KEY `idx_news_topic_name` (`topic_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻话题表';

CREATE TABLE `news` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '新闻ID',
  `title` VARCHAR(255) NOT NULL COMMENT '新闻标题',
  `summary` VARCHAR(1000) NOT NULL COMMENT '新闻摘要',
  `content` LONGTEXT NOT NULL COMMENT '新闻正文',
  `cover_image` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '封面图',
  `category_id` BIGINT UNSIGNED NOT NULL COMMENT '分类ID',
  `topic_id` BIGINT UNSIGNED NULL COMMENT '话题ID',
  `source` VARCHAR(128) NOT NULL COMMENT '来源',
  `author` VARCHAR(128) NOT NULL COMMENT '作者',
  `publish_time` DATETIME NOT NULL COMMENT '发布时间',
  `view_count` INT NOT NULL DEFAULT 0 COMMENT '浏览量',
  `like_count` INT NOT NULL DEFAULT 0 COMMENT '点赞数',
  `comment_count` INT NOT NULL DEFAULT 0 COMMENT '评论数',
  `favorite_count` INT NOT NULL DEFAULT 0 COMMENT '收藏数',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1正常，0下架，2待审核',
  `tags` JSON NULL COMMENT '标签列表',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_news_category_id` (`category_id`),
  KEY `idx_news_topic_id` (`topic_id`),
  KEY `idx_news_status_publish_time` (`status`, `publish_time`),
  KEY `idx_news_publish_time` (`publish_time`),
  FULLTEXT KEY `ft_news_title_summary_content` (`title`, `summary`, `content`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻表';

CREATE TABLE `news_comment` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '评论ID',
  `news_id` BIGINT UNSIGNED NOT NULL COMMENT '新闻ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `parent_id` BIGINT UNSIGNED NULL COMMENT '父评论ID',
  `content` TEXT NOT NULL COMMENT '评论内容',
  `like_count` INT NOT NULL DEFAULT 0 COMMENT '点赞数',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1正常，2折叠，3待审核，4删除',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_news_comment_news_id` (`news_id`),
  KEY `idx_news_comment_user_id` (`user_id`),
  KEY `idx_news_comment_parent_id` (`parent_id`),
  KEY `idx_news_comment_status_create_time` (`status`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻评论表';

CREATE TABLE `user_like` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `target_id` BIGINT UNSIGNED NOT NULL COMMENT '目标ID',
  `target_type` VARCHAR(32) NOT NULL COMMENT '目标类型：news、news_comment、community_post、post_comment',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_like_target` (`user_id`, `target_id`, `target_type`),
  KEY `idx_user_like_user_id` (`user_id`),
  KEY `idx_user_like_target_id` (`target_id`, `target_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='点赞关系表';

CREATE TABLE `favorite` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `target_id` BIGINT UNSIGNED NOT NULL COMMENT '目标ID',
  `target_type` VARCHAR(32) NOT NULL COMMENT '目标类型：news、community_post、ai_generate_record',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_favorite_target` (`user_id`, `target_id`, `target_type`),
  KEY `idx_favorite_user_id` (`user_id`),
  KEY `idx_favorite_target_id` (`target_id`, `target_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='收藏关系表';

CREATE TABLE `browse_history` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '浏览记录ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `news_id` BIGINT UNSIGNED NOT NULL COMMENT '新闻ID',
  `browse_time` DATETIME NOT NULL COMMENT '浏览时间',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_browse_history_user_id` (`user_id`),
  KEY `idx_browse_history_news_id` (`news_id`),
  KEY `idx_browse_history_browse_time` (`browse_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='浏览历史表';

CREATE TABLE `ai_generate_record` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `source_news_id` BIGINT UNSIGNED NULL COMMENT '来源新闻ID',
  `input_text` LONGTEXT NOT NULL COMMENT '输入文本',
  `title_count` INT NOT NULL DEFAULT 3 COMMENT '标题数量',
  `summary_type` VARCHAR(32) NOT NULL DEFAULT 'generate' COMMENT '摘要类型',
  `summary_style` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '摘要风格',
  `title_style` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '标题风格',
  `summary_length` VARCHAR(16) NOT NULL DEFAULT 'both' COMMENT '摘要长度',
  `candidate_titles` JSON NULL COMMENT '候选标题',
  `summary_short` LONGTEXT NULL COMMENT '短摘要',
  `summary_long` LONGTEXT NULL COMMENT '长摘要',
  `summary_points` JSON NULL COMMENT '摘要要点',
  `keywords` JSON NULL COMMENT '关键词',
  `news_elements` JSON NULL COMMENT '新闻要素',
  `risk_level` VARCHAR(16) NULL COMMENT '风险等级',
  `check_result` JSON NULL COMMENT '校验结果',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1正常，0删除',
  PRIMARY KEY (`id`),
  KEY `idx_ai_generate_record_user_id` (`user_id`),
  KEY `idx_ai_generate_record_source_news_id` (`source_news_id`),
  KEY `idx_ai_generate_record_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI 生成记录表';

CREATE TABLE `upload_file` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '文件ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `file_name` VARCHAR(255) NOT NULL COMMENT '文件名',
  `file_path` VARCHAR(500) NOT NULL COMMENT '文件路径',
  `file_type` VARCHAR(64) NOT NULL COMMENT '文件类型',
  `file_size` BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '文件大小',
  `parse_status` VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT '解析状态',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_upload_file_user_id` (`user_id`),
  KEY `idx_upload_file_parse_status` (`parse_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='上传文件表';

CREATE TABLE `community_post` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '帖子ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `title` VARCHAR(255) NOT NULL COMMENT '标题',
  `content` LONGTEXT NOT NULL COMMENT '内容',
  `related_news_id` BIGINT UNSIGNED NULL COMMENT '关联新闻ID',
  `topic_id` BIGINT UNSIGNED NULL COMMENT '关联话题ID',
  `like_count` INT NOT NULL DEFAULT 0 COMMENT '点赞数',
  `comment_count` INT NOT NULL DEFAULT 0 COMMENT '评论数',
  `favorite_count` INT NOT NULL DEFAULT 0 COMMENT '收藏数',
  `heat_score` INT NOT NULL DEFAULT 0 COMMENT '热度值',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1正常，2折叠，3待审核，4删除',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_community_post_user_id` (`user_id`),
  KEY `idx_community_post_related_news_id` (`related_news_id`),
  KEY `idx_community_post_topic_id` (`topic_id`),
  KEY `idx_community_post_status_create_time` (`status`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区帖子表';

CREATE TABLE `post_comment` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '帖子评论ID',
  `post_id` BIGINT UNSIGNED NOT NULL COMMENT '帖子ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `parent_id` BIGINT UNSIGNED NULL COMMENT '父评论ID',
  `content` TEXT NOT NULL COMMENT '评论内容',
  `like_count` INT NOT NULL DEFAULT 0 COMMENT '点赞数',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1正常，2折叠，3待审核，4删除',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_post_comment_post_id` (`post_id`),
  KEY `idx_post_comment_user_id` (`user_id`),
  KEY `idx_post_comment_parent_id` (`parent_id`),
  KEY `idx_post_comment_status_create_time` (`status`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='帖子评论表';

CREATE TABLE `user_block` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '拉黑发起用户ID',
  `blocked_user_id` BIGINT UNSIGNED NOT NULL COMMENT '被拉黑用户ID',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_block_pair` (`user_id`, `blocked_user_id`),
  KEY `idx_user_block_user_id` (`user_id`),
  KEY `idx_user_block_blocked_user_id` (`blocked_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户拉黑表';

CREATE TABLE `hot_topic` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `title` VARCHAR(255) NOT NULL COMMENT '热搜标题',
  `target_type` VARCHAR(32) NOT NULL COMMENT '目标类型：news、community_post、news_topic',
  `target_id` BIGINT UNSIGNED NOT NULL COMMENT '目标ID',
  `heat_score` INT NOT NULL DEFAULT 0 COMMENT '热度值',
  `rank_no` INT NOT NULL DEFAULT 0 COMMENT '排名',
  `tag` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '标签',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_hot_topic_target` (`target_type`, `target_id`),
  KEY `idx_hot_topic_rank_no` (`rank_no`),
  KEY `idx_hot_topic_heat_score` (`heat_score`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='热搜话题表';

CREATE TABLE `event_timeline` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `topic_id` BIGINT UNSIGNED NOT NULL COMMENT '话题ID',
  `timeline_json` JSON NOT NULL COMMENT '时间线节点JSON',
  `source_news_ids` JSON NULL COMMENT '来源新闻ID列表',
  `generate_status` VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '生成状态：pending、success、failed',
  `generated_at` DATETIME NULL COMMENT '生成时间',
  `updated_at` DATETIME NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_event_timeline_topic_id` (`topic_id`),
  KEY `idx_event_timeline_generate_status` (`generate_status`),
  KEY `idx_event_timeline_generated_at` (`generated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='事件脉络时间线缓存表';

SET FOREIGN_KEY_CHECKS = 1;

SHOW TABLES;
