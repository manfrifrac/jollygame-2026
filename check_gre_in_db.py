import sqlite3
import os

db_path = 'fluidra_clean.db'
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT count(*) FROM products WHERE taxonomy LIKE '%Gre%' OR title LIKE '%Gre%'")
        count = cursor.fetchone()[0]
        print(f"Products mentioning Gre in {db_path}: {count}")
        
        # Also check taxonomy specifically
        cursor.execute("SELECT taxonomy, count(*) FROM products GROUP BY taxonomy HAVING taxonomy LIKE '%Gre%'")
        taxonomies = cursor.fetchall()
        for tax, cnt in taxonomies:
            print(f"Taxonomy '{tax}': {cnt}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
