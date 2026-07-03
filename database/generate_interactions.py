"""Generate seed_interaction.sql for 35-user system with 10:2:3:1 ratio."""
from pathlib import Path
from datetime import datetime, timedelta
import random

random.seed(20260703)

# User variables from seed_users.sql
CORE = ['@cu1', '@cu2', '@cu3']
ACTIVE = [f'@au{i}' for i in range(1, 13)]
PASSIVE = [f'@pu{i}' for i in range(1, 16)]
SYSTEM = ['@ed', '@ad']
ORIGINAL = ['1', '2', '3']
ALL_USERS = CORE + ACTIVE + PASSIVE + SYSTEM
ALL_USERS_WITH_ORIG = ALL_USERS + ORIGINAL

# News tiers based on actual DB data
VIRAL_NEWS = [302, 304, 299, 295, 305, 283, 2, 7, 1, 273, 297, 306]
NORMAL_NEWS = [3,4,5,6,8,9,10,11,12,13,14,15,16,17,18,19,20,21,88,91,135,149,152,
               263,264,265,266,274,275,276,290,291,292,293,294,296,298,300,301,303,307]
COLD_NEWS = [184,185,186,187,188,189,249,250,251,252,253,254,255]

# Post variables from seed_content.sql (18 posts)
POSTS = [f'@p{i}' for i in range(1, 19)]

# News comment variables from seed_content.sql (50 comments)
NEWS_COMMENTS = [f'@nc{i}' for i in range(1, 51)]

# Post comment variables from seed_content.sql (20 comments)
POST_COMMENTS = [f'@pc{i}' for i in range(1, 21)]

BASE_DATE = datetime(2026, 6, 3)

def rand_date(min_day, max_day):
    d = BASE_DATE + timedelta(days=random.randint(min_day, max_day),
                               hours=random.randint(0, 23),
                               minutes=random.randint(0, 59))
    return d.strftime('%Y-%m-%d %H:%M:%S')

lines = []
lines.append("""-- ============================================================
-- Seed Phase 3: 互动数据 (浏览 + 点赞 + 收藏)
-- 35用户系统 | 比例 浏览:评论:点赞:收藏 = 10:2:3:1
-- 依赖: seed_users.sql + seed_content.sql
-- ============================================================
SET NAMES utf8mb4;

-- ============================================================
-- PART A: browse_history
-- VIRAL news: 12-15 browses each
-- NORMAL news: 2-4 browses each
-- COLD news: 0-1 browses each
-- ============================================================
""")

# --- Browse: VIRAL news ---
for news_id in VIRAL_NEWS:
    # Each viral news gets browsed by ~12 users from all tiers
    browsers = random.sample(ALL_USERS_WITH_ORIG, min(12, len(ALL_USERS_WITH_ORIG)))
    for uv in browsers:
        t = rand_date(8, 28)
        lines.append(
            f"INSERT IGNORE INTO `browse_history` (`user_id`, `news_id`, `target_type`, `target_id`, `browse_time`) "
            f"VALUES ({uv}, {news_id}, 'news', {news_id}, '{t}');"
        )

# --- Browse: NORMAL news (sampled, ~40 news get 2-5 browses) ---
sampled_normal = random.sample(NORMAL_NEWS, min(30, len(NORMAL_NEWS)))
for news_id in sampled_normal:
    n_browsers = random.randint(2, 5)
    browsers = random.sample(ALL_USERS_WITH_ORIG, n_browsers)
    for uv in browsers:
        t = rand_date(5, 28)
        lines.append(
            f"INSERT IGNORE INTO `browse_history` (`user_id`, `news_id`, `target_type`, `target_id`, `browse_time`) "
            f"VALUES ({uv}, {news_id}, 'news', {news_id}, '{t}');"
        )

# --- Browse: COLD news (1 browse each for ~10 cold news, by passive users) ---
sampled_cold = random.sample(COLD_NEWS, min(10, len(COLD_NEWS)))
for news_id in sampled_cold:
    uv = random.choice(PASSIVE)
    t = rand_date(2, 10)
    lines.append(
        f"INSERT IGNORE INTO `browse_history` (`user_id`, `news_id`, `target_type`, `target_id`, `browse_time`) "
        f"VALUES ({uv}, {news_id}, 'news', {news_id}, '{t}');"
    )

# --- Browse: Posts (each post gets 5-10 browses) ---
for pv in POSTS:
    n_browsers = random.randint(5, 10)
    browsers = random.sample(ALL_USERS, min(n_browsers, len(ALL_USERS)))
    for uv in browsers:
        t = rand_date(15, 30)
        lines.append(
            f"INSERT IGNORE INTO `browse_history` (`user_id`, `news_id`, `target_type`, `target_id`, `browse_time`) "
            f"VALUES ({uv}, 0, 'post', {pv}, '{t}');"
        )

lines.append(f"\n-- browse_history total: ~{sum(1 for l in lines if 'browse_history' in l)} records\n")

# ============================================================
# PART B: user_like (~75 records)
# ============================================================
lines.append("""
-- ============================================================
-- PART B: user_like (mixed target_type, ~75 records)
-- ============================================================
""")

# Core users: 6 likes each (mixed)
for cu in CORE:
    # 2 news likes
    for _ in range(2):
        nid = random.choice(VIRAL_NEWS[:6])
        lines.append(
            f"INSERT IGNORE INTO `user_like` (`user_id`, `target_type`, `target_id`, `created_at`) "
            f"VALUES ({cu}, 'news', {nid}, '{rand_date(12,28)}');"
        )
    # 2 comment likes
    for _ in range(2):
        ncid = random.choice(NEWS_COMMENTS[:30])
        lines.append(
            f"INSERT IGNORE INTO `user_like` (`user_id`, `target_type`, `target_id`, `created_at`) "
            f"VALUES ({cu}, 'news_comment', {ncid}, '{rand_date(12,28)}');"
        )
    # 1 post like
    pv = random.choice(POSTS[:8])
    lines.append(
        f"INSERT IGNORE INTO `user_like` (`user_id`, `target_type`, `target_id`, `created_at`) "
        f"VALUES ({cu}, 'community_post', {pv}, '{rand_date(16,30)}');"
    )
    # 1 post_comment like
    pcv = random.choice(POST_COMMENTS[:15])
    lines.append(
        f"INSERT IGNORE INTO `user_like` (`user_id`, `target_type`, `target_id`, `created_at`) "
        f"VALUES ({cu}, 'post_comment', {pcv}, '{rand_date(18,30)}');"
    )

# Active users: 3 likes each
for au in ACTIVE:
    # 1 news like + 1 comment like + 1 mixed
    nid = random.choice(VIRAL_NEWS[:8])
    lines.append(
        f"INSERT IGNORE INTO `user_like` (`user_id`, `target_type`, `target_id`, `created_at`) "
        f"VALUES ({au}, 'news', {nid}, '{rand_date(12,28)}');"
    )
    ncid = random.choice(NEWS_COMMENTS[:40])
    lines.append(
        f"INSERT IGNORE INTO `user_like` (`user_id`, `target_type`, `target_id`, `created_at`) "
        f"VALUES ({au}, 'news_comment', {ncid}, '{rand_date(13,28)}');"
    )
    if random.random() > 0.5:
        pv = random.choice(POSTS)
        lines.append(
            f"INSERT IGNORE INTO `user_like` (`user_id`, `target_type`, `target_id`, `created_at`) "
            f"VALUES ({au}, 'community_post', {pv}, '{rand_date(18,30)}');"
        )
    else:
        pcv = random.choice(POST_COMMENTS)
        lines.append(
            f"INSERT IGNORE INTO `user_like` (`user_id`, `target_type`, `target_id`, `created_at`) "
            f"VALUES ({au}, 'post_comment', {pcv}, '{rand_date(18,30)}');"
        )

# Passive users: 1-2 likes each (mostly news)
for pu in PASSIVE:
    nid = random.choice(VIRAL_NEWS[:8])
    lines.append(
        f"INSERT IGNORE INTO `user_like` (`user_id`, `target_type`, `target_id`, `created_at`) "
        f"VALUES ({pu}, 'news', {nid}, '{rand_date(15,28)}');"
    )

# System users: 2-3 likes each
for su in SYSTEM:
    for _ in range(2):
        nid = random.choice(VIRAL_NEWS[:6])
        lines.append(
            f"INSERT IGNORE INTO `user_like` (`user_id`, `target_type`, `target_id`, `created_at`) "
            f"VALUES ({su}, 'news', {nid}, '{rand_date(10,28)}');"
        )
    ncid = random.choice(NEWS_COMMENTS[:15])
    lines.append(
        f"INSERT IGNORE INTO `user_like` (`user_id`, `target_type`, `target_id`, `created_at`) "
        f"VALUES ({su}, 'news_comment', {ncid}, '{rand_date(15,28)}');"
    )

# ============================================================
# PART C: favorite (~25 records)
# ============================================================
lines.append("""
-- ============================================================
-- PART C: favorite (~25 records, news:post = 2:1)
-- ============================================================
""")

# Core users: 2 favorites each (news + post)
for cu in CORE:
    nid = random.choice(VIRAL_NEWS[:6])
    lines.append(
        f"INSERT IGNORE INTO `favorite` (`user_id`, `target_type`, `target_id`, `created_at`) "
        f"VALUES ({cu}, 'news', {nid}, '{rand_date(14,28)}');"
    )
    pv = random.choice(POSTS[:8])
    lines.append(
        f"INSERT IGNORE INTO `favorite` (`user_id`, `target_type`, `target_id`, `created_at`) "
        f"VALUES ({cu}, 'community_post', {pv}, '{rand_date(18,30)}');"
    )

# Active users: 1 favorite each (mostly news)
for au in ACTIVE:
    nid = random.choice(VIRAL_NEWS[:8])
    lines.append(
        f"INSERT IGNORE INTO `favorite` (`user_id`, `target_type`, `target_id`, `created_at`) "
        f"VALUES ({au}, 'news', {nid}, '{rand_date(14,28)}');"
    )

# Passive users: ~8 have 1 favorite each
for pu in random.sample(PASSIVE, 8):
    nid = random.choice(VIRAL_NEWS[:8])
    lines.append(
        f"INSERT IGNORE INTO `favorite` (`user_id`, `target_type`, `target_id`, `created_at`) "
        f"VALUES ({pu}, 'news', {nid}, '{rand_date(18,28)}');"
    )

# System users: 1 each
for su in SYSTEM:
    nid = random.choice(VIRAL_NEWS[:4])
    lines.append(
        f"INSERT IGNORE INTO `favorite` (`user_id`, `target_type`, `target_id`, `created_at`) "
        f"VALUES ({su}, 'news', {nid}, '{rand_date(15,28)}');"
    )

lines.append("\nSELECT 'seed_interaction.sql completed' AS status;\n")

# Write file
output = Path(__file__).resolve().parent / "seeds" / "seed_interaction.sql"
output.write_text('\n'.join(lines), encoding='utf-8')

# Stats
like_count = sum(1 for l in lines if 'user_like' in l)
fav_count = sum(1 for l in lines if 'favorite' in l)
browse_count = sum(1 for l in lines if 'browse_history' in l)
print(f"Generated: {browse_count} browses, {like_count} likes, {fav_count} favorites")
print(f"Written to: {output}")
