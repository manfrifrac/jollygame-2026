import sqlite3
import os

ROOT_PATH = r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame'
DB_FILES = {
    'fluidra': os.path.join(ROOT_PATH, 'fluidra_clean.db'),
    'bestway': os.path.join(ROOT_PATH, 'bestway_clean.db'),
    'intex': os.path.join(ROOT_PATH, 'intex_clean.db')
}

for name, path in DB_FILES.items():
    if not os.path.exists(path):
        print(f"❌ {name} DB not found at {path}")
        continue
    print(f"\n--- Schema for {name.upper()} ---")
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for t in tables:
        table_name = t[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        info = cursor.fetchall()
        cols = [col[1] for col in info]
        print(f"Table {table_name}: {cols}")
    conn.close()
