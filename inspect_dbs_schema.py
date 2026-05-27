import sqlite3
import json

def inspect_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"--- {db_path} ---")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"Table: {table_name} ({count} rows)")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    conn.close()

dbs = ["fluidra_catalog.db", "intex_catalog.db", "bestway_catalog.db", "bestway_clean.db", "intex_clean.db", "fluidra_clean.db"]
for db in dbs:
    try:
        inspect_db(db)
    except Exception as e:
        print(f"Error inspecting {db}: {e}")
