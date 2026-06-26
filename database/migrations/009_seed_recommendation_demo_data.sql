-- ============================================================================
-- 个性化推荐演示数据
--
-- 目的：为普通用户 user/123456 补充浏览、点赞、收藏记录，
-- 使其能明显看到推荐效果（科技相关新闻优先推荐）。
--
-- 执行前检查：
-- 1. 确保 user 表中存在用户 'user'
-- 2. 确保 news_category 表中存在科技类分类
-- 3. 确保 news 表中有科技类新闻
-- ============================================================================

-- 为了避免重复插入，使用 INSERT IGNORE 或检查是否已存在
-- 注意：此脚本是幂等的，可以安全地重复执行

SET FOREIGN_KEY_CHECKS = 0;

-- 获取普通用户 ID（用户名为 'user'）
SET @user_id = (SELECT id FROM user WHERE username = 'user' LIMIT 1);

-- 获取科技分类 ID
SET @tech_category_id = (SELECT id FROM news_category WHERE name LIKE '%科技%' OR name = '科技' LIMIT 1);

-- 如果找不到科技分类，尝试获取第一个分类（演示用）
IF @tech_category_id IS NULL THEN
  SET @tech_category_id = (SELECT id FROM news_category WHERE status = 1 LIMIT 1);
END IF;

-- 只在找到用户和分类时执行以下操作
-- ============================================================================
-- 步骤 1：为用户添加浏览记录（科技类新闻）
-- ============================================================================

IF @user_id IS NOT NULL AND @tech_category_id IS NOT NULL THEN

  -- 为用户添加 5 条科技类新闻的浏览记录（权重：1分）
  INSERT IGNORE INTO browse_history (user_id, news_id, browse_time)
  SELECT
    @user_id,
    n.id,
    DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 7) DAY) as browse_time
  FROM news n
  WHERE n.category_id = @tech_category_id
    AND n.status = 1
    AND n.id NOT IN (
      SELECT news_id FROM browse_history
      WHERE user_id = @user_id
    )
  LIMIT 5;

-- ============================================================================
-- 步骤 2：为用户添加点赞记录（科技类新闻）
-- ============================================================================

  -- 为用户添加 2 条科技类新闻的点赞记录（权重：3分）
  INSERT IGNORE INTO user_like (user_id, target_type, target_id, created_at)
  SELECT
    @user_id,
    'news',
    n.id,
    DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 5) DAY) as created_at
  FROM news n
  WHERE n.category_id = @tech_category_id
    AND n.status = 1
    AND n.id NOT IN (
      SELECT target_id FROM user_like
      WHERE user_id = @user_id AND target_type = 'news'
    )
  LIMIT 2;

-- ============================================================================
-- 步骤 3：为用户添加收藏记录（科技类新闻）
-- ============================================================================

  -- 为用户添加 1 条科技类新闻的收藏记录（权重：5分）
  INSERT IGNORE INTO favorite (user_id, target_type, target_id, created_at)
  SELECT
    @user_id,
    'news',
    n.id,
    DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 3) DAY) as created_at
  FROM news n
  WHERE n.category_id = @tech_category_id
    AND n.status = 1
    AND n.id NOT IN (
      SELECT target_id FROM favorite
      WHERE user_id = @user_id AND target_type = 'news'
    )
  LIMIT 1;

END IF;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- 演示数据补齐完成
--
-- 效果说明：
-- 1. 用户浏览了科技类新闻（affinity = 5 * 1 = 5）
-- 2. 用户点赞了科技类新闻（affinity += 2 * 3 = 11）
-- 3. 用户收藏了科技类新闻（affinity += 1 * 5 = 16）
-- 4. 总 affinity = 16（科技分类）
-- 5. 推荐时会优先推荐同科技分类下的其他新闻
-- 6. 推荐理由："因为你经常阅读「科技」分类新闻"
-- ============================================================================
