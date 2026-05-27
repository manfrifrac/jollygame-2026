import sqlite3
import json
import os

def check_db(db_path):
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vediamo le tabelle
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        results = {}
        for table in tables:
            t_name = table[0]
            # Cerchiamo colonne che sembrano nomi o prezzi
            cursor.execute(f"PRAGMA table_info({t_name})")
            cols = [c[1] for f in cursor.fetchall()]
            
            # Recuperiamo un campione
            cursor.execute(f"SELECT * FROM {t_name} LIMIT 100")
            rows = cursor.fetchall()
            results[t_name] = {"columns": cols, "data": rows}
            
        conn.close()
        return results
    except Exception as e:
        return str(e)

dbs = ["fluidra_catalog.db", "bestway_catalog.db", "fluidra_clean.db", "bestway_clean.db"]
report = {}

for db in dbs:
    print(f"Checking {db}...")
    report[db] = check_db(db)

with open("db_inspection_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print("Inspection complete. Saved to db_inspection_report.json")
