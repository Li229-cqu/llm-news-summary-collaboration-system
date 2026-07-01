SET FOREIGN_KEY_CHECKS = 0;

SET @user_id := (SELECT id FROM `user` WHERE username = 'user' LIMIT 1);
SET @tech_category_id := (
  SELECT id
  FROM `news_category`
  WHERE name LIKE '%科技%' OR name = '科技'
  LIMIT 1
);
SET @tech_category_id := COALESCE(
  @tech_category_id,
  (SELECT id FROM `news_category` WHERE status = 1 LIMIT 1)
);

INSERT IGNORE INTO `browse_history` (`user_id`, `news_id`, `browse_time`)
SELECT
  @user_id,
  n.id,
  DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 7) DAY)
FROM `news` n
WHERE @user_id IS NOT NULL
  AND @tech_category_id IS NOT NULL
  AND n.category_id = @tech_category_id
  AND n.status = 1
  AND n.id NOT IN (
    SELECT news_id FROM `browse_history`
    WHERE user_id = @user_id
  )
LIMIT 5;

INSERT IGNORE INTO `user_like` (`user_id`, `target_type`, `target_id`, `created_at`)
SELECT
  @user_id,
  'news',
  n.id,
  DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 5) DAY)
FROM `news` n
WHERE @user_id IS NOT NULL
  AND @tech_category_id IS NOT NULL
  AND n.category_id = @tech_category_id
  AND n.status = 1
  AND n.id NOT IN (
    SELECT target_id FROM `user_like`
    WHERE user_id = @user_id AND target_type = 'news'
  )
LIMIT 2;

INSERT IGNORE INTO `favorite` (`user_id`, `target_type`, `target_id`, `created_at`)
SELECT
  @user_id,
  'news',
  n.id,
  DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 3) DAY)
FROM `news` n
WHERE @user_id IS NOT NULL
  AND @tech_category_id IS NOT NULL
  AND n.category_id = @tech_category_id
  AND n.status = 1
  AND n.id NOT IN (
    SELECT target_id FROM `favorite`
    WHERE user_id = @user_id AND target_type = 'news'
  )
LIMIT 1;

SET FOREIGN_KEY_CHECKS = 1;
