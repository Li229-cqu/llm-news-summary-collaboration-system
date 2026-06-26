USE llm_news_system;

-- DB12 修复：当前后端新闻模块与爬虫脚本以 news.editor 为准。
-- 旧版本本地数据库可能仍使用 news.author，导致查询失败并 fallback 到 mock。
-- 本迁移可重复执行：缺少 editor 时新增字段，并尽量从 author 迁移已有数据。

SET @editor_exists := (
  SELECT COUNT(1)
  FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'news'
    AND column_name = 'editor'
);

SET @source_url_exists := (
  SELECT COUNT(1)
  FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'news'
    AND column_name = 'source_url'
);

SET @sql := IF(
  @editor_exists = 0 AND @source_url_exists > 0,
  'ALTER TABLE `news` ADD COLUMN `editor` VARCHAR(128) DEFAULT NULL COMMENT ''新闻编辑'' AFTER `source_url`',
  IF(
    @editor_exists = 0,
    'ALTER TABLE `news` ADD COLUMN `editor` VARCHAR(128) DEFAULT NULL COMMENT ''新闻编辑'' AFTER `source`',
    'SELECT 1'
  )
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @author_exists := (
  SELECT COUNT(1)
  FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'news'
    AND column_name = 'author'
);

SET @editor_exists := (
  SELECT COUNT(1)
  FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'news'
    AND column_name = 'editor'
);

SET @sql := IF(
  @author_exists > 0 AND @editor_exists > 0,
  'UPDATE `news` SET `editor` = `author` WHERE (`editor` IS NULL OR `editor` = '''') AND `author` IS NOT NULL AND `author` <> ''''',
  'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 旧表中的 author 可能是 NOT NULL 且没有默认值。
-- 当前代码不再写 author，如果不放宽该字段，新爬取新闻会因为缺少 author 插入失败。
SET @author_exists := (
  SELECT COUNT(1)
  FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'news'
    AND column_name = 'author'
);

SET @sql := IF(
  @author_exists > 0,
  'ALTER TABLE `news` MODIFY COLUMN `author` VARCHAR(128) DEFAULT NULL COMMENT ''旧版作者字段，当前兼容保留''',
  'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT column_name, column_type, is_nullable
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND table_name = 'news'
  AND column_name IN ('author', 'editor', 'source_url')
ORDER BY ordinal_position;
