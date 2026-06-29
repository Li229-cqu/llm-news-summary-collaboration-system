-- 为 news 表的 title、summary、content 字段建立 FULLTEXT 全文索引
-- 使用 ngram 分词器支持中文搜索
-- 适用于 MySQL 8.0+
-- 执行前请确认 MySQL 版本 >= 8.0

ALTER TABLE `news`
  ADD FULLTEXT INDEX `ft_news_search` (`title`, `summary`, `content`)
  WITH PARSER ngram;
