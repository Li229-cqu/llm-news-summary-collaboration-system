-- 为新闻评论表新增富媒体字段
ALTER TABLE `news_comment`
  ADD COLUMN IF NOT EXISTS `media_json` JSON NULL COMMENT '评论媒体信息' AFTER `content`;

