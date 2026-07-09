# scripts/crawlers

本目录包含项目本地新闻爬虫脚本，从多个新闻网站抓取文章并写入 MySQL `news` 表。所有爬虫统一读取 `backend/.env` 中的数据库配置，优先使用 `source_url` 去重。

## 脚本一览

| 脚本 | 目标网站 | 抓取方式 | 覆盖频道 |
| --- | --- | --- | --- |
| `rss_news_crawler.py` | 光明网 `gmw.cn` | RSS 源 + 详情页正文解析 | 时政、国际、财经、社会、文化/娱乐、科技、体育 |
| `news_cn_crawler.py` | 新华网 `news.cn` | RSS 源 + 详情页正文解析 | 时政、国际、财经、科技、健康、娱乐、地方、法治、评论 |
| `people_cn_crawler.py` | 人民网 `people.com.cn` | RSS 源 + 详情页正文解析 | 时政、社会、财经、科技、体育、文娱、国际 |
| `gmw_7days_test_crawler.py` | 光明网 7 天历史测试 | RSS 源，可回填近 7 天新闻 | — |

## 通用命令行参数

所有正式爬虫（`rss_news_crawler.py`、`news_cn_crawler.py`、`people_cn_crawler.py`）支持相同的命令行参数：

| 参数 | 说明 |
| --- | --- |
| `--limit-per-source N` | 每个频道最多抓取篇数（默认各脚本不同，通常 10-30） |
| `--since-days N` | 仅保留最近 N 天内的新闻，0 表示不过滤 |
| `--dry-run` | 预览不写库 |
| `--fetch-content` | 抓取文章详情页正文（默认启用） |
| `--update-existing` | 更新已有新闻的正文和 cover_image（不重置点赞、收藏等互动数据） |

## 人民网爬虫（people_cn_crawler.py）

从人民网各频道 RSS 源抓取新闻，覆盖时政、社会、财经、科技、体育、文娱、国际 7 个频道。

### 特点

- 自动检测页面编码（UTF-8 / GBK / GB2312 / GB18030），兼容人民网各子站的不同编码。
- 正文解析：优先定位 `.rm_txt_con` → `.text_con` → `#articleContent` 容器，提取 `<p>` 标签长文本。
- 图片过滤：自动排除 logo、icon、二维码、微信/微博分享图、GIF 动图等非内容图片。
- 封面图去重：入库前检查图片是否已被其他不同文章使用，避免重复封面。
- 时间解析：优先使用页面 `<meta name="publishdate">` 和可见时间标签，兜底从 URL 提取日期。
- `--since-days` 过滤基于文章发布时间，不是抓取时间。

### 运行命令

预览抓取，不入库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\people_cn_crawler.py --limit-per-source 10 --dry-run
```

正式入库（每个频道最多 10 篇）：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\people_cn_crawler.py --limit-per-source 10
```

仅保留最近 3 天的新闻：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\people_cn_crawler.py --limit-per-source 10 --since-days 3
```

更新已有新闻的正文和图片：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\people_cn_crawler.py --limit-per-source 10 --update-existing
```

## 光明网爬虫（rss_news_crawler.py）

预览抓取，不入库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --limit-per-source 30 --fetch-content --dry-run
```

正式入库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --limit-per-source 30 --fetch-content
```

更新已有新闻的正文和图片：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --limit-per-source 30 --fetch-content --update-existing
```

## 新华网爬虫（news_cn_crawler.py）

预览抓取，不入库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\news_cn_crawler.py --limit-per-source 10 --dry-run
```

正式入库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\news_cn_crawler.py --limit-per-source 10
```

## 定时执行建议

### 方案一：Windows 任务计划程序（推荐）

建议每 15-30 分钟执行一次。以人民网爬虫为例：

- 程序/脚本：`<项目根>\backend\.venv\Scripts\python.exe`
- 参数：`scripts\crawlers\people_cn_crawler.py --limit-per-source 10 --since-days 1`
- 起始于：`<项目根>`

其他爬虫类似替换脚本名和参数即可。

### 方案二：PowerShell 循环（仅开发测试）

```powershell
while ($true) {
  backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --limit-per-source 10
  backend\.venv\Scripts\python.exe scripts\crawlers\news_cn_crawler.py --limit-per-source 10
  backend\.venv\Scripts\python.exe scripts\crawlers\people_cn_crawler.py --limit-per-source 10
  Start-Sleep -Seconds 900
}
```

## 注意事项

- 运行前请确保 `database/schema.sql` 和 `database/seed.sql` 已导入，`backend/.env` 中的数据库配置正确。
- 各爬虫按 `source_url` 去重，相同 URL 的文章不会重复入库。
- 建议每次抓取条数不要太大，通常每源 5-10 条即可，避免触发反爬。
- 不建议把无限循环写进 FastAPI 服务里，爬虫应作为独立离线任务运行。
- 部分频道使用 JS 动态渲染，RSS 可能覆盖不到所有文章。
- 封面图只保存 URL，不下载文件到本地。入库时会检查图片是否已被其他文章用作封面，避免多篇文章共用同一张图。
