import sqlite3
import json
import os
import urllib.request
from pathlib import Path

products = [
    "FREERIDER", "RF 5200 iQ",
    "VOYAGER", "RE 4400 iQ", "RE 45AM iQ", "RE 4300", "RE 4700 iQ",
    "Tornax", "OT 3200", "PRO RT 3200", "PRO RT 2100",
    "ALPHA iQ", "RA 6700 iQ", "RA 6570 iQ",
    "XA TYPE", "XA 2010",
    "MX8 BARACUDA",
    "WERUNNER PLUS", "Electric Vac", "action vac",
    "niya tracker 25", "niya tracker 35", "Niya Sonar 30", "Niya Eclipse 35",
    "tracker 25", "tracker 35", "Sonar 30", "Eclipse 35"
]

output_dir = "depliant"
os.makedirs(output_dir, exist_ok=True)

def download_file(url, filename):
    filepath = os.path.join(output_dir, filename)
    if os.path.exists(filepath):
        print(f"Already downloaded: {filename}")
        return
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        print(f"Downloaded: {filename}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

print("\n--- Checking fluidra_clean.db ---")
try:
    conn = sqlite3.connect('fluidra_clean.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT title, docs_json FROM products")
    for row in cursor.fetchall():
        title, docs_json = row
        if not title or not docs_json: continue
        
        for p in products:
            if p.lower() in title.lower():
                try:
                    docs = json.loads(docs_json)
                    for doc in docs:
                        doc_url = doc.get('url', '')
                        doc_name = doc.get('name', 'doc')
                        if doc_url.endswith('.pdf') or 'bynder' in doc_url or 'dam.fluidra' in doc_url:
                            safe_name = "".join([c if c.isalnum() else "_" for c in f"{p}_{doc_name}"]) + ".pdf"
                            print(f"Match: {title} -> {doc_name}")
                            download_file(doc_url, safe_name)
                except Exception as e:
                    pass
                break
    conn.close()
except Exception as e:
    print(f"Error: {e}")
