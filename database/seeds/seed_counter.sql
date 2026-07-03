-- ============================================================
-- Seed Phase 4: Counter 回算 (事后一致性修复)
-- 依赖: Phase 1~3 全部数据落库
-- 原则: 所有 counter 通过子查询回算，不写死数值
-- ============================================================
SET NAMES utf8mb4;

-- ============================================================
-- Step 1: 评论级 like_count (底层, 先算)
-- ============================================================

-- news_comment.like_count ← user_like
UPDATE `news_comment` nc
SET nc.`like_count` = (
    SELECT COUNT(*)
    FROM `user_like` ul
    WHERE ul.`target_type` = 'news_comment'
      AND ul.`target_id` = nc.`id`
)
WHERE nc.`id` IN (
    SELECT DISTINCT ul.`target_id`
    FROM `user_like` ul
    WHERE ul.`target_type` = 'news_comment'
);

-- post_comment.like_count ← user_like
UPDATE `post_comment` pc
SET pc.`like_count` = (
    SELECT COUNT(*)
    FROM `user_like` ul
    WHERE ul.`target_type` = 'post_comment'
      AND ul.`target_id` = pc.`id`
)
WHERE pc.`id` IN (
    SELECT DISTINCT ul.`target_id`
    FROM `user_like` ul
    WHERE ul.`target_type` = 'post_comment'
);

-- ============================================================
-- Step 2: 新闻/帖子级 like_count (依赖 user_like)
-- ============================================================

-- news.like_count ← user_like
UPDATE `news` n
SET n.`like_count` = GREATEST((
    SELECT COUNT(*)
    FROM `user_like` ul
    WHERE ul.`target_type` = 'news'
      AND ul.`target_id` = n.`id`
), 0);

-- community_post.like_count ← user_like
UPDATE `community_post` p
SET p.`like_count` = GREATEST((
    SELECT COUNT(*)
    FROM `user_like` ul
    WHERE ul.`target_type` = 'community_post'
      AND ul.`target_id` = p.`id`
), 0);

-- ============================================================
-- Step 3: 新闻/帖子级 comment_count (依赖评论表)
-- ============================================================

-- news.comment_count ← news_comment (status IN 1,2)
UPDATE `news` n
SET n.`comment_count` = GREATEST((
    SELECT COUNT(*)
    FROM `news_comment` nc
    WHERE nc.`news_id` = n.`id`
      AND nc.`status` IN (1, 2)
), 0);

-- community_post.comment_count ← post_comment (status IN 1,2)
UPDATE `community_post` p
SET p.`comment_count` = GREATEST((
    SELECT COUNT(*)
    FROM `post_comment` pc
    WHERE pc.`post_id` = p.`id`
      AND pc.`status` IN (1, 2)
), 0);

-- ============================================================
-- Step 4: 新闻/帖子级 favorite_count (依赖 favorite 表)
-- ============================================================

-- news.favorite_count ← favorite
UPDATE `news` n
SET n.`favorite_count` = GREATEST((
    SELECT COUNT(*)
    FROM `favorite` f
    WHERE f.`target_type` = 'news'
      AND f.`target_id` = n.`id`
), 0);

-- community_post.favorite_count ← favorite
UPDATE `community_post` p
SET p.`favorite_count` = GREATEST((
    SELECT COUNT(*)
    FROM `favorite` f
    WHERE f.`target_type` = 'community_post'
      AND f.`target_id` = p.`id`
), 0);

-- ============================================================
-- Step 5: 新闻/帖子级 view_count (依赖 browse_history)
-- ============================================================

-- news.view_count ← browse_history (target_type='news')
UPDATE `news` n
SET n.`view_count` = GREATEST((
    SELECT COUNT(*)
    FROM `browse_history` bh
    WHERE bh.`target_type` = 'news'
      AND bh.`target_id` = n.`id`
), 0);

-- community_post.view_count ← browse_history (target_type='post')
UPDATE `community_post` p
SET p.`view_count` = GREATEST((
    SELECT COUNT(*)
    FROM `browse_history` bh
    WHERE bh.`target_type` = 'post'
      AND bh.`target_id` = p.`id`
), 0);

-- ============================================================
-- Step 6: community_post.heat_score (依赖以上所有 counter)
-- 公式: heat_score = like*10 + comment*8 + favorite*5 + view*2
-- ============================================================
UPDATE `community_post` p
SET p.`heat_score` = GREATEST(
    p.`like_count` * 10
    + p.`comment_count` * 8
    + p.`favorite_count` * 5
    + p.`view_count` * 2,
    0
);

-- ============================================================
-- Step 7: 验证摘要
-- ============================================================
SELECT
    '=== Counter Recalculation Summary ===' AS message
UNION ALL
SELECT CONCAT('news rows updated: ', COUNT(*))
FROM `news`
WHERE `status` = 1
UNION ALL
SELECT CONCAT('community_post updated: ', COUNT(*))
FROM `community_post`
UNION ALL
SELECT CONCAT('news_comment likes updated: ', COUNT(*))
FROM `news_comment` nc
INNER JOIN `user_like` ul ON ul.`target_type` = 'news_comment' AND ul.`target_id` = nc.`id`
UNION ALL
SELECT CONCAT('post_comment likes updated: ', COUNT(*))
FROM `post_comment` pc
INNER JOIN `user_like` ul ON ul.`target_type` = 'post_comment' AND ul.`target_id` = pc.`id`
UNION ALL
SELECT 'seed_counter.sql completed';

-- ============================================================
-- 热点新闻抽查 (viral news #302, #304)
-- ============================================================
SELECT
    n.id,
    n.title,
    n.view_count,
    n.like_count,
    n.comment_count,
    n.favorite_count,
    (n.like_count + n.comment_count + n.favorite_count + n.view_count) AS total_interactions
FROM `news` n
WHERE n.id IN (302, 304, 2, 7, 1)
ORDER BY total_interactions DESC;
