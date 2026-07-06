from __future__ import annotations

import os

import pymysql
from dotenv import load_dotenv

load_dotenv()
load_dotenv("backend/.env", override=True)


def main() -> None:
    connection = pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "llm_news_user"),
        password=os.getenv("DB_PASSWORD", "123456"),
        database=os.getenv("DB_NAME", "llm_news_system"),
        charset="utf8mb4",
        autocommit=False,
    )
    try:
        with connection.cursor() as cursor:
            where_sql = """
                (
                    REPLACE(REPLACE(REPLACE(LOWER(config_key), '_', ''), '-', ''), ' ', '') LIKE %s
                    OR REPLACE(REPLACE(REPLACE(LOWER(config_key), '_', ''), '-', ''), ' ', '') LIKE %s
                    OR LOWER(config_key) LIKE %s
                )
            """
            params = ("%apikey%", "%secretkey%", "%token%")
            cursor.execute(
                f"""
                SELECT config_key, COALESCE(CHAR_LENGTH(config_value), 0) AS value_length
                FROM system_config
                WHERE {where_sql}
                ORDER BY config_key
                """
                ,
                params,
            )
            rows = cursor.fetchall()
            affected = cursor.execute(
                f"""
                DELETE FROM system_config
                WHERE {where_sql}
                """,
                params,
            )
        connection.commit()
        print(f"Matched {len(rows)} sensitive system_config row(s).")
        for key, value_length in rows:
            print(f"  {key}: value_length={value_length}")
        print(f"Deleted {affected} sensitive system_config row(s).")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
