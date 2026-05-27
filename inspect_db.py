import sqlite3
import json

def inspect_db(db_path):
    print(f"--- Inspecting {db_path} ---")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables:", tables)
        
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print("Columns:", [col[1] for col in columns])
            
            # Check for R0516700 in any text column
            for col in columns:
                if col[2] in ('TEXT', 'VARCHAR'):
                    cursor.execute(f"SELECT * FROM {table_name} WHERE {col[1]} LIKE '%R0516700%' LIMIT 2;")
                    results = cursor.fetchall()
                    if results:
                        print(f"Found in {col[1]}:", results)
                        
    except Exception as e:
        print("Error:", e)

inspect_db('fluidra_catalog.db')
inspect_db('fluidra_clean.db')
