@echo off
REM 每日自动爬虫脚本（可用于 Windows 任务计划程序）
REM 建议每天 6:00 AM 执行一次
set "PROJECT_DIR=C:\Users\huan\Downloads\llm-news-summary-collaboration-system-develop (1)\llm-news-summary-collaboration-system-develop"
set "PYTHON=%PROJECT_DIR%\backend\.venv\Scripts\python.exe"
set "CRAWLER=%PROJECT_DIR%\scripts\crawlers\rss_news_crawler.py"
set "LOGFILE=%PROJECT_DIR%\scripts\crawlers\auto_crawl.log"

echo [%date% %time%] Auto crawl starting... >> "%LOGFILE%"
"%PYTHON%" "%CRAWLER%" --max-items 10 --fetch-content >> "%LOGFILE%" 2>&1
echo [%date% %time%] Auto crawl done. >> "%LOGFILE%"
