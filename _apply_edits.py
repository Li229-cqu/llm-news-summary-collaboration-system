import re

path = r'd:\自用\学习\大三下\项目实训\llm-news-summary-collaboration-system\frontend\src\views\admin\AdminView.vue'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add timelines to sectionTitles (after hotTopics line)
old1 = "hotTopics: '热搜与话题管理',\n  users: '用户管理',"
new1 = "hotTopics: '热搜与话题管理',\n  timelines: 'Timeline 管理',\n  users: '用户管理',"
content = content.replace(old1, new1, 1)

# 2. Add timelines to sidebarSections (after hotTopics entry)
old2 = "{ key: 'hotTopics', label: '热搜与话题管理', icon: TrendCharts },\n  { key: 'users', label: '用户管理', icon: UserFilled },"
new2 = "{ key: 'hotTopics', label: '热搜与话题管理', icon: TrendCharts },\n  { key: 'timelines', label: 'Timeline 管理', icon: TrendCharts },\n  { key: 'users', label: '用户管理', icon: UserFilled },"
content = content.replace(old2, new2, 1)

# 3. Add timelines case in loadSection switch
old3 = "case 'hotTopics':\n      break\n    case 'users':"
new3 = "case 'hotTopics':\n      break\n    case 'timelines':\n      break\n    case 'users':"
content = content.replace(old3, new3, 1)

# 4. Add AdminTimelineManagement component in template (after AdminHotTopicManagement block)
old4 = "<AdminHotTopicManagement\n            v-if=\"activeTab === 'hotTopics'\"\n            @changed=\"loadDashboard\"\n          />\n\n          <el-card v-if=\"activeTab === 'users'\""
new4 = "<AdminHotTopicManagement\n            v-if=\"activeTab === 'hotTopics'\"\n            @changed=\"loadDashboard\"\n          />\n\n          <AdminTimelineManagement\n            v-if=\"activeTab === 'timelines'\"\n            @changed=\"loadDashboard\"\n          />\n\n          <el-card v-if=\"activeTab === 'users'\""
content = content.replace(old4, new4, 1)

# 5. Update editorQuickEntries timeline-refresh from coming-soon to available
old5 = "'timeline-refresh',\n    title: 'Timeline 管理',\n    description: '查看事件脉络相关任务状态',\n    icon: TrendCharts,\n    status: 'coming-soon',"
new5 = "'timeline-refresh',\n    title: 'Timeline 管理',\n    description: '查看事件脉络相关任务状态',\n    icon: TrendCharts,\n    targetTab: 'timelines',\n    status: 'available',"
content = content.replace(old5, new5, 1)

# 6. Update todoCards timeline-refresh from disabled to available
old6 = "'timeline-refresh',\n    title: 'Timeline 管理',\n    count: '--',\n    hint: '该模块将在后续阶段接入真实业务接口',\n    disabled: true,"
new6 = "'timeline-refresh',\n    title: 'Timeline 管理',\n    count: '--',\n    hint: '进入 Timeline 管理页面',\n    targetTab: 'timelines',\n    disabled: false,"
content = content.replace(old6, new6, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("All edits applied successfully!")
