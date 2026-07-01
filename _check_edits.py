import json

path = r'd:\自用\学习\大三下\项目实训\llm-news-summary-collaboration-system\frontend\src\views\admin\AdminView.vue'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

edits = []

# 1. Add timelines to sectionTitles
old1 = "hotTopics: '热搜与话题管理',\n  users: '用户管理',"
new1 = "hotTopics: '热搜与话题管理',\n  timelines: 'Timeline 管理',\n  users: '用户管理',"
count1 = content.count(old1)
edits.append(('sectionTitles', count1, old1[:80]))

# 2. Add timelines to sidebarSections
old2 = "{ key: 'hotTopics', label: '热搜与话题管理', icon: TrendCharts },\n  { key: 'users', label: '用户管理', icon: UserFilled },"
new2 = "{ key: 'hotTopics', label: '热搜与话题管理', icon: TrendCharts },\n  { key: 'timelines', label: 'Timeline 管理', icon: TrendCharts },\n  { key: 'users', label: '用户管理', icon: UserFilled },"
count2 = content.count(old2)
edits.append(('sidebarSections', count2, old2[:80]))

# 3. Add timelines case in loadSection switch
old3 = "case 'hotTopics':\n      break\n    case 'users':"
new3 = "case 'hotTopics':\n      break\n    case 'timelines':\n      break\n    case 'users':"
count3 = content.count(old3)
edits.append(('loadSection case', count3, old3[:80]))

# 4. Add AdminTimelineManagement in template
old4 = "<AdminHotTopicManagement\n            v-if=\"activeTab === 'hotTopics'\"\n            @changed=\"loadDashboard\"\n          />\n\n          <el-card v-if=\"activeTab === 'users'\""
new4 = "<AdminHotTopicManagement\n            v-if=\"activeTab === 'hotTopics'\"\n            @changed=\"loadDashboard\"\n          />\n\n          <AdminTimelineManagement\n            v-if=\"activeTab === 'timelines'\"\n            @changed=\"loadDashboard\"\n          />\n\n          <el-card v-if=\"activeTab === 'users'\""
count4 = content.count(old4)
edits.append(('template component', count4, old4[:80]))

# 5. Update editorQuickEntries timeline-refresh
old5 = "'timeline-refresh',\n    title: 'Timeline 管理',\n    description: '查看事件脉络相关任务状态',\n    icon: TrendCharts,\n    status: 'coming-soon',"
new5 = "'timeline-refresh',\n    title: 'Timeline 管理',\n    description: '查看事件脉络相关任务状态',\n    icon: TrendCharts,\n    targetTab: 'timelines',\n    status: 'available',"
count5 = content.count(old5)
edits.append(('editorQuickEntries', count5, old5[:80]))

# 6. Update todoCards timeline-refresh
old6 = "'timeline-refresh',\n    title: 'Timeline 管理',\n    count: '--',\n    hint: '该模块将在后续阶段接入真实业务接口',\n    disabled: true,"
new6 = "'timeline-refresh',\n    title: 'Timeline 管理',\n    count: '--',\n    hint: '进入 Timeline 管理页面',\n    targetTab: 'timelines',\n    disabled: false,"
count6 = content.count(old6)
edits.append(('todoCards', count6, old6[:80]))

# Print counts
for name, count, snippet in edits:
    print(f'{name}: count={count} | {snippet}...')
