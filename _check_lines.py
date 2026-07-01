with open(r'd:\自用\学习\大三下\项目实训\llm-news-summary-collaboration-system\frontend\src\views\admin\AdminView.vue', 'r', encoding='utf-8') as f:
    content = f.read()
lines = content.split('\n')
for i in range(125, 145):
    print(f'{i+1}: {repr(lines[i])}')
