"""Update all SQL queries in get_weekly_report to exclude today."""
with open('d:/大三下/实训/project/test/backend/app/modules/profile/service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# All queries need: >= start AND < end_exclusive
# Pattern: each browse_time >= %s or created_at >= %s needs a < %s added

# browse queries (2 occurrences)
content = content.replace(
    "browse_time>=%s\n           AND (target_type='news' OR target_type IS NULL OR target_type='')",
    "browse_time>=%s AND browse_time<%s\n           AND (target_type='news' OR target_type IS NULL OR target_type='')"
)
content = content.replace(
    "browse_time>=%s\n           WHERE user_id=%s AND target_type='post' AND target_id IS NOT NULL",
    "browse_time>=%s AND browse_time<%s\n           WHERE user_id=%s AND target_type='post' AND target_id IS NOT NULL"
)

# fav queries
content = content.replace(
    "f.user_id=%s AND f.target_type='news' AND f.created_at>=%s",
    "f.user_id=%s AND f.target_type='news' AND f.created_at>=%s AND f.created_at<%s"
)
content = content.replace(
    "f.user_id=%s AND f.target_type='post' AND f.created_at>=%s",
    "f.user_id=%s AND f.target_type='post' AND f.created_at>=%s AND f.created_at<%s"
)

# comment queries
content = content.replace(
    "news_comment WHERE user_id=%s AND status<>4 AND created_at>=%s",
    "news_comment WHERE user_id=%s AND status<>4 AND created_at>=%s AND created_at<%s"
)
content = content.replace(
    "post_comment WHERE user_id=%s AND status<>4 AND created_at>=%s",
    "post_comment WHERE user_id=%s AND status<>4 AND created_at>=%s AND created_at<%s"
)

# AI query
content = content.replace(
    "ai_generate_record WHERE user_id=%s AND status=1 AND created_at>=%s",
    "ai_generate_record WHERE user_id=%s AND status=1 AND created_at>=%s AND created_at<%s"
)

# topic_rank browse queries
content = content.replace(
    "bh.browse_time>=%s\n          AND (bh.target_type='news' OR bh.target_type IS NULL OR bh.target_type='')",
    "bh.browse_time>=%s AND bh.browse_time<%s\n          AND (bh.target_type='news' OR bh.target_type IS NULL OR bh.target_type='')"
)
content = content.replace(
    "bh.browse_time>=%s\n        GROUP BY name ORDER BY cnt DESC",
    "bh.browse_time>=%s AND bh.browse_time<%s\n        GROUP BY name ORDER BY cnt DESC"
)

# Update params for all these queries - add end_exclusive to the params list
# The browse queries use [user_id, start_date_str] → [user_id, start_date_str, end_exclusive]
import re

# Find param lists like [user_id, start_date_str] that come after the modified queries
# and add end_exclusive
params_to_update = [
    ('[user_id, start_date_str],\n    )\n    browse_count', '[user_id, start_date_str, end_exclusive],\n    )\n    browse_count'),
    ('[user_id, start_date_str],\n        )\n        # Add post', '[user_id, start_date_str, end_exclusive],\n        )\n        # Add post'),
    ('[user_id, start_date_str],\n    )\n    favorite_count', '[user_id, start_date_str, end_exclusive],\n    )\n    favorite_count'),
    ('[user_id, start_date_str],\n    )\n    pc', '[user_id, start_date_str, end_exclusive],\n    )\n    pc'),
    ('[user_id, start_date_str],\n    )\n    ai_count', '[user_id, start_date_str, end_exclusive],\n    )\n    ai_count'),
    ('[user_id, start_date_str],\n    )\n    # Add post tags', '[user_id, start_date_str, end_exclusive],\n    )\n    # Add post tags'),
]

for old_p, new_p in params_to_update:
    content = content.replace(old_p, new_p)

# Also need to fix the separate fav_news and fav_post params
content = content.replace(
    "[user_id, start_date_str],\n    )\n    favorite_count",
    "[user_id, start_date_str, end_exclusive],\n    )\n    favorite_count"
)

# Update daily_activity loop
content = content.replace(
    "for i in range(6, -1, -1):\n        d = (today - timedelta(days=i)).isoformat()",
    "for i in range(6, -1, -1):\n        d = (end_date - timedelta(days=i)).isoformat()"
)

# Also fix: the earlier "news_comment" query in overview section needs end_exclusive
# The one after "pc =" needs updating too
content = content.replace(
    "\"SELECT COUNT(*) AS cnt FROM news_comment WHERE user_id=%s AND status<>4 AND created_at>=%s AND created_at<%s\",\n        [user_id, start_date_str],\n    )\n    pc",
    "\"SELECT COUNT(*) AS cnt FROM news_comment WHERE user_id=%s AND status<>4 AND created_at>=%s AND created_at<%s\",\n        [user_id, start_date_str, end_exclusive],\n    )\n    pc"
)

# Fix the comment_count section - the nc query needs end_exclusive in params
content = content.replace(
    "\"SELECT COUNT(*) AS cnt FROM news_comment WHERE user_id=%s AND status<>4 AND created_at>=%s AND created_at<%s\",\n        [user_id, start_date_str],\n    )",
    "\"SELECT COUNT(*) AS cnt FROM news_comment WHERE user_id=%s AND status<>4 AND created_at>=%s AND created_at<%s\",\n        [user_id, start_date_str, end_exclusive],\n    )"
)
content = content.replace(
    "\"SELECT COUNT(*) AS cnt FROM post_comment WHERE user_id=%s AND status<>4 AND created_at>=%s AND created_at<%s\",\n        [user_id, start_date_str],\n    )",
    "\"SELECT COUNT(*) AS cnt FROM post_comment WHERE user_id=%s AND status<>4 AND created_at>=%s AND created_at<%s\",\n        [user_id, start_date_str, end_exclusive],\n    )"
)
content = content.replace(
    "\"SELECT COUNT(*) AS cnt FROM ai_generate_record WHERE user_id=%s AND status=1 AND created_at>=%s AND created_at<%s\",\n        [user_id, start_date_str],\n    )\n    ai_count",
    "\"SELECT COUNT(*) AS cnt FROM ai_generate_record WHERE user_id=%s AND status=1 AND created_at>=%s AND created_at<%s\",\n        [user_id, start_date_str, end_exclusive],\n    )\n    ai_count"
)

with open('d:/大三下/实训/project/test/backend/app/modules/profile/service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('All SQL queries and params updated')
