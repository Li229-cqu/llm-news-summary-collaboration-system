import os
from pathlib import Path

import pymysql


config = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "llm_news_user"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "llm_news_system"),
    "charset": "utf8mb4",
    "autocommit": False,
}


IGNORABLE_ERRORS = (
    "Duplicate column name",
    "Duplicate key name",
    "Duplicate entry",
    "already exists",
    "Can't DROP",
)


def split_sql(sql_content: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False

    for char in sql_content:
        current.append(char)

        if escaped:
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue

        if quote:
            if char == quote:
                quote = None
            continue

        if char in ("'", '"', "`"):
            quote = char
            continue

        if char == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement[:-1].strip())
            current = []

    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)

    return statements


def execute_sql_file(filepath: Path) -> None:
    sql_content = filepath.read_text(encoding="utf-8-sig")
    statements = split_sql(sql_content)

    conn = None
    try:
        conn = pymysql.connect(**config)
        cursor = conn.cursor()

        for stmt in statements:
            if not stmt:
                continue
            try:
                cursor.execute(stmt)
                print(f"OK: {stmt[:80].replace(os.linesep, ' ')}...")
            except pymysql.Error as exc:
                message = str(exc)
                if any(token in message for token in IGNORABLE_ERRORS):
                    print(f"SKIP: {stmt[:80].replace(os.linesep, ' ')}... ({message})")
                    continue
                conn.rollback()
                raise

        conn.commit()
        print(f"Migration finished: {filepath.name}")
    except pymysql.Error as exc:
        print(f"Migration failed: {filepath.name}")
        print(f"Error: {exc}")
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    migrations_dir = Path(__file__).resolve().parent / "migrations"
    migration_files = sorted(path for path in migrations_dir.iterdir() if path.suffix == ".sql")

    print("Database migrations:")
    for index, path in enumerate(migration_files, start=1):
        print(f"  {index}. {path.name}")

    print("\nRunning migrations...")
    for index, path in enumerate(migration_files, start=1):
        print(f"\n--- [{index}/{len(migration_files)}] {path.name} ---")
        execute_sql_file(path)

    print("\nAll migrations finished.")
