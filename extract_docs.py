import csv
import sqlite3
import json

products = [
    "FREERIDER", "RF 5200 iQ",
    "VOYAGER", "RE 4400 iQ", "RE 45AM iQ", "RE 4300", "RE 4700 iQ",
    "Tornax", "OT 3200", "PRO RT 3200", "PRO RT 2100",
    "ALPHA iQ", "RA 6700 iQ", "RA 6570 iQ",
    "XA TYPE", "XA 2010",
    "MX8 BARACUDA",
    "WERUNNER PLUS", "Electric Vac", "action vac",
    "niya tracker 25", "niya tracker 35", "Niya Sonar 30", "Niya Eclipse 35"
]

print("--- Checking zodiac_enriched_data.csv ---")
with open('zodiac_enriched_data.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        title = row.get('Titolo', '')
        for p in products:
            if p.lower() in title.lower():
                docs = row.get('PDF_Documents', '')
                if docs:
                    print(f"Match: {title}")
                    print(f"  Docs: {docs}")
                break

print("\n--- Checking fluidra_clean.db ---")
try:
    conn = sqlite3.connect('fluidra_clean.db')
    cursor = conn.cursor()
    # Find table name
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    if tables:
        table_name = tables[0][0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        print("Columns:", columns)
        
        # Check if we have title/name and pdf/docs
        if 'titolo' in columns and 'documenti' in columns:
            cursor.execute(f"SELECT titolo, documenti FROM {table_name}")
            for row in cursor.fetchall():
                title, docs = row
                if not title: continue
                for p in products:
                    if p.lower() in title.lower() and docs and docs != "[]":
                        print(f"Match: {title}")
                        print(f"  Docs: {docs}")
                        break
        elif 'title' in columns and 'pdf' in columns:
             cursor.execute(f"SELECT title, pdf FROM {table_name}")
             for row in cursor.fetchall():
                title, docs = row
                if not title: continue
                for p in products:
                    if p.lower() in title.lower() and docs and docs != "[]":
                        print(f"Match: {title}")
                        print(f"  Docs: {docs}")
                        break
    conn.close()
except Exception as e:
    print(f"Error: {e}")

print("\n--- Checking fluidra_catalog.db ---")
try:
    conn = sqlite3.connect('fluidra_catalog.db')
    cursor = conn.cursor()
    # Find table name
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    if tables:
        table_name = tables[0][0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        print("Columns:", columns)
        
        # Check if we have title/name and pdf/docs
        if 'title' in columns and 'pdfs' in columns:
            cursor.execute(f"SELECT title, pdfs FROM {table_name}")
            for row in cursor.fetchall():
                title, docs = row
                if not title: continue
                for p in products:
                    if p.lower() in title.lower() and docs and docs != "[]":
                        print(f"Match: {title}")
                        print(f"  Docs: {docs}")
                        break
        elif 'nome' in columns and 'documenti' in columns:
            cursor.execute(f"SELECT nome, documenti FROM {table_name}")
            for row in cursor.fetchall():
                title, docs = row
                if not title: continue
                for p in products:
                    if p.lower() in title.lower() and docs and docs != "[]":
                        print(f"Match: {title}")
                        print(f"  Docs: {docs}")
                        break
    conn.close()
except Exception as e:
    print(f"Error: {e}")
