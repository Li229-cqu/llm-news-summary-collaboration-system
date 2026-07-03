# 光明网 RSS 新闻爬虫使用说明

## 爬虫定位

只爬取光明网（Guangming Daily / gmw.cn），不包含中国新闻网和人民网。

## 支持分类

| 分类码 | 中文名 | RSS URL |
|---|---|---|
| politics | 时政 | news.gmw.cn/rss_news.xml |
| world | 国际 | world.gmw.cn/rss_world.xml |
| finance | 财经 | economy.gmw.cn/rss_economy.xml |
| society | 社会 | life.gmw.cn/rss_life.xml |
| entertainment | 娱乐 | culture.gmw.cn/rss_culture.xml |
| technology | 科技 | tech.gmw.cn/rss_tech.xml |
| sports | 体育 | sports.gmw.cn/rss_sports.xml |

## 环境准备

```bash
pip install -r backend/requirements.txt
```

需要：requests, feedparser, pymysql, python-dotenv, beautifulsoup4

## 数据库准备

```sql
CREATE DATABASE IF NOT EXISTS news_summary_system_demo
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 导入表结构
mysql -u root -p news_summary_system_demo < database/schema.sql

-- 初始化分类
INSERT INTO news_category (name, code, sort, status) VALUES
('推荐','recommend',1,1),('时政','politics',2,1),('社会','society',3,1),
('财经','finance',4,1),('科技','technology',5,1),('体育','sports',6,1),
('娱乐','entertainment',7,1),('国际','world',8,1);
```

配置 `.env`：
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=news_summary_system_demo
```

## 正式爬虫（写入 news 表）

```bash
# dry-run 预览
python scripts/crawlers/rss_news_crawler.py --limit-per-source 30 --fetch-content --dry-run

# 正式写入
python scripts/crawlers/rss_news_crawler.py --limit-per-source 30 --fetch-content
```

## 7天历史测试（写入测试表）

```bash
# dry-run
python scripts/crawlers/gmw_7days_test_crawler.py --limit 50

# 写入测试表
python scripts/crawlers/gmw_7days_test_crawler.py --limit 100 --apply --reset
```

## 常见问题

- **分类不存在**：确保已执行分类初始化 SQL
- **数据库连接失败**：检查 .env 配置
- **RSS 访问失败**：检查网络，gmw.cn 需可达
- **正文过短跳过**：MIN_CONTENT_LENGTH=200 过滤，正常现象
- **图片为空**：光明网部分文章无配图，正常现象

## 注意事项

- 不再支持中国新闻网和人民网
- 文化(culture)频道映射到娱乐(entertainment)分类
- 已移除健康(health)分类，科技使用 technology 分类
