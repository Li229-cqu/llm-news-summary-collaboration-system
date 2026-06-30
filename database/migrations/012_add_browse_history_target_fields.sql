-- 为浏览历史表增加 target_type / target_id 字段，支持帖子浏览记录
-- 已存在的记录保持 target_type = 'news'，news_id 仍正常使用

ALTER TABLE `browse_history`
  ADD COLUMN IF NOT EXISTS `target_type` VARCHAR(64) DEFAULT 'news' COMMENT '浏览目标类型' AFTER `news_id`;

ALTER TABLE `browse_history`
  ADD COLUMN IF NOT EXISTS `target_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '浏览目标ID（帖子时使用）' AFTER `target_type`;

-- 允许 news_id 为 0（帖子浏览无对应 news_id）
ALTER TABLE `browse_history`
  MODIFY COLUMN `news_id` BIGINT UNSIGNED NOT NULL DEFAULT 0;

-- 为帖子浏览查询建索引
ALTER TABLE `browse_history`
  ADD INDEX IF NOT EXISTS `idx_browse_history_target` (`user_id`, `target_type`, `target_id`);
