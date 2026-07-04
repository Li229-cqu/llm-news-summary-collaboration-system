"""Run all seed SQL files in sequence on a single DB connection."""
import os, sys
from pathlib import Path
import pymysql

config = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "llm_news_user"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "llm_news_system"),
    "charset": "utf8mb4",
    "autocommit": True,
}

SKIP_ERRORS = (
    "Duplicate column name",
    "Duplicate key name",
    "Duplicate entry",
    "already exists",
    "Can't DROP",
    "Unknown column",
)

def split_sql(sql_content):
    """Split SQL into statements, respecting quotes."""
    statements = []
    current = []
    in_string = False
    quote_char = None
    escaped = False

    for char in sql_content:
        current.append(char)
        if escaped:
            escaped = False
            continue
        if char == '\\':
            escaped = True
            continue
        if in_string:
            if char == quote_char:
                in_string = False
            continue
        if char in ("'", '"', '`'):
            in_string = True
            quote_char = char
            continue
        if char == ';':
            stmt = ''.join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []

    trailing = ''.join(current).strip()
    if trailing:
        statements.append(trailing)
    return statements


def run_seed_file(cursor, filepath):
    print(f'\n{"="*60}')
    print(f'Running: {filepath.name}')
    print(f'{"="*60}')
    sql_content = filepath.read_text(encoding="utf-8-sig")
    statements = split_sql(sql_content)

    ok_count = 0
    skip_count = 0
    for i, stmt in enumerate(statements):
        if not stmt or stmt.isspace():
            continue
        try:
            cursor.execute(stmt)
            ok_count += 1
            # Print SELECT results
            upper = stmt.strip().upper()
            if upper.startswith('SELECT'):
                try:
                    rows = cursor.fetchall()
                    if rows:
                        for row in rows:
                            print(f'  {row}')
                except Exception:
                    pass
        except pymysql.Error as exc:
            message = str(exc)
            if any(token in message for token in SKIP_ERRORS):
                skip_count += 1
                preview = stmt[:100].replace('\n', ' ').replace('\r', '')
                print(f'  SKIP: {preview}... ({message[:80]})')
            else:
                print(f'  ERROR at stmt #{i+1}: {message}')
                print(f'  SQL: {stmt[:300]}')
                raise
    print(f'  OK={ok_count}, SKIP={skip_count}')


def main():
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    try:
        seed_dir = Path(__file__).resolve().parent / "seeds"
        # MUST run in dependency order: users → content → interaction → counter
        ordered_names = [
            'seed_users.sql',
            'seed_content.sql',
            'seed_interaction.sql',
            'seed_counter.sql',
        ]
        files = []
        for name in ordered_names:
            fpath = seed_dir / name
            if fpath.exists():
                files.append(fpath)
            else:
                print(f"WARNING: {name} not found, skipping")

        if not files:
            print("No seed files found!")
            sys.exit(1)

        print(f"Seed files to run: {[f.name for f in files]}")
        for f in files:
            run_seed_file(cursor, f)

        print(f'\n{"="*60}')
        print('All seed files executed successfully!')
        print(f'{"="*60}')

        # Final verification
        print('\n--- Final Data Summary ---')
        for table in ['user', 'community_post', 'news_comment', 'post_comment',
                       'browse_history', 'user_like', 'favorite']:
            cursor.execute(f'SELECT COUNT(*) FROM `{table}`')
            print(f'  {table}: {cursor.fetchone()[0]} rows')

        # Check viral news counter consistency
        print('\n--- Hot News Check ---')
        cursor.execute("""
            SELECT id, title, view_count, like_count, comment_count, favorite_count
            FROM news WHERE id IN (302, 304, 2, 1) ORDER BY id
        """)
        for row in cursor.fetchall():
            print(f'  news#{row[0]}: views={row[2]} likes={row[3]} comments={row[4]} favs={row[5]} | {row[1][:40]}')

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
