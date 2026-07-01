import pymysql
import os

config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'llm_news_user',
    'password': '123456',
    'database': 'llm_news_system',
    'charset': 'utf8mb4',
}

def execute_sql_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    statements = sql_content.split(';')
    
    conn = None
    try:
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                try:
                    cursor.execute(stmt)
                    print(f"✓ 执行成功: {stmt[:50]}...")
                except pymysql.Error as e:
                    if "Duplicate column name" in str(e) or "Table 'event' already exists" in str(e):
                        print(f"⚠ 已存在，跳过: {stmt[:50]}...")
                    elif "Duplicate key name" in str(e):
                        print(f"⚠ 索引已存在，跳过: {stmt[:50]}...")
                    else:
                        print(f"✗ 执行失败: {stmt[:50]}...")
                        print(f"  错误: {str(e)}")
        
        conn.commit()
        print(f"\n✅ 迁移文件 {os.path.basename(filepath)} 执行完成")
    except pymysql.Error as e:
        print(f"\n❌ 数据库连接失败: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    migrations_dir = os.path.dirname(os.path.abspath(__file__)) + '/migrations'
    
    migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
    
    print("📋 数据库迁移脚本列表:")
    for i, f in enumerate(migration_files):
        print(f"  {i+1}. {f}")
    
    print("\n🚀 开始执行数据库迁移...")
    
    for i, filename in enumerate(migration_files):
        filepath = os.path.join(migrations_dir, filename)
        print(f"\n--- [{i+1}/{len(migration_files)}] 执行 {filename} ---")
        execute_sql_file(filepath)
    
    print("\n🎉 所有迁移脚本执行完成!")
