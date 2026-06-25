# scripts/crawlers

这里放项目本地新闻爬虫脚本。当前第一版使用 RSS 源抓取新闻，不做网页深度正文解析。

## 当前说明

- 使用公开 RSS 源获取新闻标题、摘要、链接、发布时间、来源和分类。
- 当前会优先抓取原文页面正文，抓不到时回退到 RSS 摘要或描述。
- 运行前请先执行 `database/schema.sql` 和 `database/seed.sql`。
- 爬虫会从 `backend/.env` 读取数据库连接配置。
- 当前脚本支持：
  - `--dry-run` 仅预览，不写数据库
  - `--max-items` 控制每个 RSS 源最多抓取多少条
  - `--source` 选择 `china_news` 或 `all`
  - `--cleanup-days` 将多少天前的新闻置为归档状态（`status = 0`）

## 脚本位置

- `scripts/crawlers/rss_news_crawler.py`

## 运行命令

预览解析结果，不写数据库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --dry-run --max-items 3
```

正式入库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --max-items 5
```

归档 30 天前的旧新闻：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --max-items 5 --cleanup-days 30
```

## 定时执行建议

### 方案一：Windows 任务计划程序（推荐）

建议每 15 分钟执行一次：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --max-items 5
```

建议配置：

- 程序/脚本：
  `D:\自用\学习\大三下\项目实训\llm-news-summary-collaboration-system\backend\.venv\Scripts\python.exe`
- 参数：
  `scripts\crawlers\rss_news_crawler.py --max-items 5`
- 起始于：
  `D:\自用\学习\大三下\项目实训\llm-news-summary-collaboration-system`

### 方案二：PowerShell 循环（仅开发测试）

```powershell
while ($true) {
  backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --max-items 5
  Start-Sleep -Seconds 900
}
```

## 当前限制

- 第一版会尝试抓取原文页面正文，但如果原文页结构复杂或无法访问，`content` 仍可能回退到摘要加链接。
- 脚本优先按 `source_url` 去重；如果没有 `source_url`，则按标题去重。
- 为了演示稳定性，建议每次抓取条数不要太大，通常每源 5 到 10 条即可。
- 不建议把无限循环写进 FastAPI 服务里。
- 后续如需扩展，可以增加人民网、新华网等更多 RSS 源。

## DB12 真实新闻展示修复说明

- 爬虫会清洗 `source_url`，只保留合法的 `http` / `https` 原文链接。
- 使用 `--fetch-content` 时，爬虫会尝试解析新闻详情页正文，并过滤侧边栏、推荐阅读、广告、上一篇/下一篇等噪声内容。
- 正文解析失败时会使用 RSS 摘要兜底，不再把“原文链接：xxx”拼进 `content`。
- 爬虫会尝试提取 `cover_image`，优先使用 RSS 媒体字段、`og:image`、`twitter:image` 和正文首图。
- 当前只保存图片 URL，不下载图片文件到本地。
- 使用 `--update-existing-content` 时，会尝试补全已有新闻的正文、封面图和原文链接，不会重置点赞、收藏、评论、浏览量。

常用命令：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --dry-run --max-items 3 --fetch-content
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --max-items 5 --fetch-content
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --max-items 20 --fetch-content --update-existing-content
```
