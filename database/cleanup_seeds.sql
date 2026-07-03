-- Cleanup: remove seed data from Phases 1-4
-- Run BEFORE re-executing seed files in correct order
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Phase 3 data (interactions) - delete first
DELETE FROM browse_history WHERE user_id NOT IN (1,2,3);
DELETE FROM user_like WHERE user_id NOT IN (1,2,3);
DELETE FROM favorite WHERE user_id NOT IN (1,2,3);

-- Phase 2 data (content)
DELETE FROM post_comment WHERE post_id >= 9 OR user_id NOT IN (1,2,3);
DELETE FROM news_comment WHERE user_id NOT IN (1,2,3);
DELETE FROM community_post WHERE user_id NOT IN (1,2,3);

-- Phase 1 data (users)
DELETE FROM user WHERE id NOT IN (1,2,3);

SET FOREIGN_KEY_CHECKS = 1;
SELECT 'Cleanup complete' AS status;
