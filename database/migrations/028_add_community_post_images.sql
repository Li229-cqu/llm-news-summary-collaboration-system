-- Add images JSON column to community_post for post image support
-- Migration: 024_add_community_post_images.sql

ALTER TABLE community_post
  ADD COLUMN `images` JSON DEFAULT NULL COMMENT '帖子图片URL列表' AFTER `tags`;
