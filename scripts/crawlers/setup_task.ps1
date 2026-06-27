$action = New-ScheduledTaskAction -Execute "C:\Users\huan\Downloads\llm-news-summary-collaboration-system-develop (1)\llm-news-summary-collaboration-system-develop\scripts\crawlers\auto_crawl.bat"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650)
$principal = New-ScheduledTaskPrincipal -UserId (whoami) -RunLevel Highest
Register-ScheduledTask -TaskName "LLM_News_Crawler" -Action $action -Trigger $trigger -Principal $principal -Force
Write-Host "Task LLM_News_Crawler created successfully!"
