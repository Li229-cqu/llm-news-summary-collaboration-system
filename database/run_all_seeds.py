"""Run the complete 35-user seed pipeline with proper SQL parsing."""
import os, sys
from pathlib import Path
import pymysql

config = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "llm_news_system"),
    "charset": "utf8mb4",
    "autocommit": False,
}

SKIP_ERRORS = (
    "Duplicate column name", "Duplicate key name", "Duplicate entry",
    "already exists", "Can't DROP", "Unknown column", "doesn't exist",
)


def split_sql(sql_content):
    """Split SQL by semicolons, respecting string/identifier quotes."""
    statements = []
    current = []
    quote = None
    escaped = False

    for char in sql_content:
        current.append(char)
        if escaped:
            escaped = False
            continue
        if char == '\\':
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = None
            continue
        if char in ("'", '"', '`'):
            quote = char
            continue
        if char == ';':
            stmt = ''.join(current).strip()
            if stmt:
                statements.append(stmt[:-1].strip())
            current = []

    trailing = ''.join(current).strip()
    if trailing:
        statements.append(trailing)
    return statements


def run_file(cursor, filepath):
    print(f'\n{"="*50}')
    print(f'Running: {filepath.name}')
    sql_content = Path(filepath).read_text(encoding="utf-8-sig")
    statements = split_sql(sql_content)
    ok = skip = err = 0
    for stmt in statements:
        if not stmt:
            continue
        try:
            cursor.execute(stmt)
            ok += 1
        except pymysql.Error as exc:
            message = str(exc)
            if any(token in message for token in SKIP_ERRORS):
                skip += 1
                if skip <= 5:
                    preview = stmt[:100].replace('\n', ' ')
                    print(f'  SKIP: {preview}...')
            else:
                err += 1
                print(f'  ERROR: {message[:200]}')
                print(f'  SQL: {stmt[:300]}')
                raise
    print(f'  OK={ok} SKIP={skip} ERR={err}')


def main():
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    base = Path(__file__).resolve().parent

    try:
        # ---- Step 0: Cleanup ----
        print("Cleaning up old seed data...")
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        cursor.execute("DELETE FROM browse_history WHERE id > 5")
        cursor.execute("DELETE FROM user_like WHERE id > 8")
        cursor.execute("DELETE FROM favorite WHERE id > 7")
        cursor.execute("DELETE FROM post_comment WHERE id > 10")
        cursor.execute("DELETE FROM news_comment WHERE id > 3")
        cursor.execute("DELETE FROM community_post WHERE id > 8")
        cursor.execute("DELETE FROM user WHERE id > 3")
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        conn.commit()

        # ---- Step 1: Restore base seed ----
        print("Restoring base seed.sql...")
        run_file(cursor, base / "seed.sql")
        conn.commit()

        # ---- Step 2: Run seed files in order ----
        seed_dir = base / "seeds"
        for fname in ["seed_users.sql", "seed_content.sql",
                       "seed_interaction.sql", "seed_counter.sql"]:
            run_file(cursor, seed_dir / fname)
            conn.commit()

        # ---- Step 3: Orphan cleanup ----
        print("\nCleaning orphan records...")
        cursor.execute(
            "DELETE FROM browse_history WHERE user_id NOT IN "
            "(SELECT id FROM (SELECT id FROM user) AS u)"
        )
        print(f"  browse_history orphans: {cursor.rowcount}")
        cursor.execute(
            "DELETE FROM user_like WHERE user_id NOT IN "
            "(SELECT id FROM (SELECT id FROM user) AS u)"
        )
        print(f"  user_like orphans: {cursor.rowcount}")
        cursor.execute(
            "DELETE FROM favorite WHERE user_id NOT IN "
            "(SELECT id FROM (SELECT id FROM user) AS u)"
        )
        print(f"  favorite orphans: {cursor.rowcount}")
        conn.commit()

        # ---- Step 4: Re-run counter (to fix after orphan cleanup) ----
        print("\nRe-running counter...")
        run_file(cursor, seed_dir / "seed_counter.sql")
        conn.commit()

        # ---- Final Report ----
        print(f"\n{'='*50}")
        print("FINAL REPORT")
        print(f"{'='*50}")
        for t in ['user', 'community_post', 'news_comment', 'post_comment',
                   'browse_history', 'user_like', 'favorite']:
            cursor.execute(f"SELECT COUNT(*) FROM `{t}`")
            print(f"  {t:25s}: {cursor.fetchone()[0]:>5}")

        # User breakdown
        cursor.execute(
            "SELECT role, COUNT(*) FROM user GROUP BY role ORDER BY role"
        )
        print("\n  User roles:")
        for row in cursor.fetchall():
            print(f"    {row[0]:10s}: {row[1]}")

        # Viral news
        print("\n  Viral News (80/20 check):")
        cursor.execute(
            "SELECT id, view_count, like_count, comment_count, favorite_count "
            "FROM news WHERE id IN (302,304,299,295,305,283,2,7,1,273) "
            "ORDER BY (view_count+like_count+comment_count+favorite_count) DESC"
        )
        for row in cursor.fetchall():
            total = sum(row[1:])
            print(f"    #{row[0]:>4}: v={row[1]:>3} l={row[2]:>2} "
                  f"c={row[3]:>2} f={row[4]:>2} total={total}")

        # Top posts
        print("\n  Top Posts:")
        cursor.execute(
            "SELECT id, user_id, like_count, comment_count, view_count, heat_score "
            "FROM community_post WHERE id > 8 "
            "ORDER BY heat_score DESC LIMIT 5"
        )
        for row in cursor.fetchall():
            print(f"    post#{row[0]} uid={row[1]}: "
                  f"likes={row[2]} comments={row[3]} "
                  f"views={row[4]} heat={row[5]}")

    except Exception as e:
        conn.rollback()
        print(f"\nFATAL: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

    print("\nDone!")


if __name__ == "__main__":
    main()
