# 爬虫管理页入口已添加到 AdminView
# 每日自动爬虫统计已添加到爬虫管理页
# 需要手动运行爬虫时：访问 /admin/crawler-test 点击"开始测试爬取"

Write-Output "===== 开始每日自动爬取 ====="
$projectRoot = "C:\Users\huan\Downloads\llm-news-summary-collaboration-system-develop (1)\llm-news-summary-collaboration-system-develop"
$pythonExe = "$projectRoot\backend\.venv\Scripts\python.exe"
$crawlerScript = "$projectRoot\scripts\crawlers\rss_news_crawler.py"
$logFile = "$projectRoot\scripts\crawlers\auto_crawl.log"

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Output "[$timestamp] 开始爬取..."
& $pythonExe $crawlerScript --max-items 10 --fetch-content *>> $logFile
Write-Output "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 爬取完成"
Write-Output "日志文件: $logFile"
