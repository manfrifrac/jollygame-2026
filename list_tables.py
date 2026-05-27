import sqlite3
import os

dbs = ['fluidra_catalog.db', 'intex_catalog.db', 'bestway_catalog.db', 'intex_deep_catalog.db']

for db in dbs:
    if os.path.exists(db):
        print(f"\n--- Database: {db} ---")
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            count = cursor.fetchone()[0]
            print(f"Tabella: {t} | Righe: {count}")
        conn.close()
