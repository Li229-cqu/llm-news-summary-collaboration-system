-- 目的：为 community_post 表添加 view_count 字段，支持真实的帖子浏览计数

ALTER TABLE `community_post`
  ADD COLUMN `view_count` INT NOT NULL DEFAULT 0 COMMENT '浏览次数' AFTER `favorite_count`;

ALTER TABLE `community_post`
  ADD KEY `idx_community_post_view_count` (`view_count`);