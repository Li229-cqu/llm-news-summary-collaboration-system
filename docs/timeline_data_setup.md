# Timeline 事件脉络 — 数据扩充与复现说明

## 背景

项目最初 `news_topic` 表只有 3 条 seed/demo 数据（id=1,2,3），`news` 表虽有 580 条真实新闻但只有 15 条分配了 `topic_id`（仅 2.6%），导致 `/timeline` 页面长期只显示相同的 3 个话题。

为了让事件脉络功能真正可用，需要补充 `news_topic`、批量分配 `news.topic_id`、为每个有效话题生成 `event_timeline` 缓存。

## 涉及脚本

### 1. `scripts/assign_news_topics.py`

根据预定义候选话题及其关键词，扫描未归类新闻并匹配。

```bash
# 预览匹配结果（不写库）
python scripts/assign_news_topics.py --dry-run

# 写入数据库（需二次 YES 确认）
python scripts/assign_news_topics.py --apply --confirm

# 小批量测试
python scripts/assign_news_topics.py --apply --confirm --limit 20
```

- 默认只处理 `topic_id IS NULL` 的新闻，不覆盖已有分配
- 支持 `--force` 覆盖（慎用）
- 15 个候选话题内置于脚本 `TOPIC_CANDIDATES` 列表中

### 2. `scripts/generate_timelines.py`

为 `news_count >= 2` 的 topic 调用后端 generate 接口生成 `event_timeline`。

```bash
# 预览待生成 topic
python scripts/generate_timelines.py --dry-run

# 执行生成（需二次 YES 确认）
python scripts/generate_timelines.py --run

# 指定 topic
python scripts/generate_timelines.py --run --topic-ids 14,15,16
```

- 需要后端服务运行中（默认 `http://localhost:8000`）
- 生成接口需要登录认证，脚本需携带 Bearer token

## 已执行结果

| 指标 | 执行前 | 执行后 |
|---|---|---|
| `news_topic` 数量 | 3 | **18** |
| 已分配 `topic_id` 的新闻 | 15 | **179** |
| `event_timeline` 数量 | 3 | **17** |
| 孤立记录 (topic_id=1004) | 1 | **0** |
| 可生成脉络的话题 | 2 | **17** |

Topic 3（新能源汽车与智能交通）因仅有 1 篇新闻，未生成 timeline，符合预期。

## 复现步骤

如果你在新环境（或重建数据库后）需要复现数据扩充：

### 1. 备份

```bash
mysqldump -u <user> -p <db> news_topic event_timeline > backup_before.sql
mysql -u <user> -p <db> -e "SELECT id, topic_id FROM news" > backup_mapping.csv
```

### 2. Dry-run 预览

```bash
python scripts/assign_news_topics.py --dry-run
```

检查输出：确认 15 个候选话题均有 >=2 条匹配，无明显误匹配。

### 3. Apply 写入

```bash
python scripts/assign_news_topics.py --apply --confirm
# 输入 YES 确认
```

### 4. 抽查修正

```bash
# 查询各 topic 下的新闻标题，人工检查误分配
# 对明确误分配的新闻执行:
# UPDATE news SET topic_id = NULL WHERE id = <id> AND topic_id = <topic_id>;
```

### 5. 生成 event_timeline

```bash
# 先 dry-run 确认待生成列表
python scripts/generate_timelines.py --dry-run

# 执行生成（需要后端服务和登录 token）
python scripts/generate_timelines.py --run
# 输入 YES 确认
```

### 6. 验证

```bash
# 确认 event_timeline 状态
mysql -u <user> -p <db> -e "
  SELECT topic_id, generate_status
  FROM event_timeline
  ORDER BY topic_id;
"
```

打开 `/timeline` 页面，确认显示 18 个话题。

## 注意事项

1. **数据库数据不是 Git 代码**：`news_topic` 和 `event_timeline` 是数据库内容，切换环境后需要重新执行脚本或导入 SQL 备份
2. **不要跳过 dry-run**：apply 前必须先 dry-run 预览，确认匹配质量
3. **不要使用 `--force`**：默认只处理 `topic_id IS NULL` 的新闻，避免覆盖已有正确分配
4. **备份是必须的**：apply 前一定先备份相关表
5. **event_timeline 生成依赖后端**：后端服务和 AI 服务需要正常运行
6. **关键词匹配有局限性**：当前为简单的 substring 匹配 + min_score + exclude 机制，少量误匹配是正常的，需要人工抽查修正
7. **候选话题列表**：脚本内置 15 个 topic，如需新增话题可编辑 `TOPIC_CANDIDATES` 后重新 dry-run → apply
