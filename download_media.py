import sqlite3
import json
import os
import requests
import concurrent.futures
from urllib.parse import urlparse
import re
import hashlib

# Cartelle di destinazione
BASE_DIR = os.path.join(os.getcwd(), "downloads")
IMAGE_DIR = os.path.join(BASE_DIR, "images")
DOC_DIR = os.path.join(BASE_DIR, "docs")

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(DOC_DIR, exist_ok=True)

def sanitize_filename(filename):
    """Rimuove caratteri non validi per i nomi dei file su Windows."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def download_file(url, folder, filename):
    """Scarica un file e lo salva con il nome specificato."""
    if not url or url == "N/A" or not url.startswith("http"): return False
    
    filename = sanitize_filename(filename)
    path = os.path.join(folder, filename)
    
    if os.path.exists(path):
        return True

    try:
        # User-Agent per evitare blocchi base
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        else:
            print(f"⚠️ Status {response.status_code} per {url}")
    except Exception as e:
        print(f"❌ Errore download {url}: {e}")
    return False

def process_product(sku, images_json, docs_json, url):
    """Elabora i media di un singolo prodotto."""
    try:
        # Se lo SKU è mancante o non valido, usiamo un hash dell'URL
        if not sku or sku == "N/A":
            sku = hashlib.md5(url.encode()).hexdigest()[:10]
        
        sku = sanitize_filename(sku)
        
        images = json.loads(images_json)
        docs = json.loads(docs_json)
        
        # Download Immagini
        for i, img_url in enumerate(images):
            ext = os.path.splitext(urlparse(img_url).path)[1] or ".jpg"
            if "?" in ext: ext = ext.split("?")[0]
            filename = f"{sku}_{i+1}{ext}"
            download_file(img_url, IMAGE_DIR, filename)
            
        # Download Documenti
        for doc in docs:
            doc_url = doc.get('url')
            doc_name = doc.get('name', 'doc').replace(" ", "_").replace("/", "_")
            if doc_url:
                ext = os.path.splitext(urlparse(doc_url).path)[1] or ".pdf"
                if "?" in ext: ext = ext.split("?")[0]
                filename = f"{sku}_{doc_name}{ext}"
                download_file(doc_url, DOC_DIR, filename)
        
        return sku
    except Exception as e:
        print(f"❌ Errore processamento {sku}: {e}")
        return None

def main():
    conn = sqlite3.connect('fluidra_catalog.db')
    cursor = conn.cursor()
    cursor.execute("SELECT sku, images_json, docs_json, url FROM products WHERE images_json != '[]' OR docs_json != '[]'")
    rows = cursor.fetchall()
    conn.close()

    print(f"🎬 Avvio download media per {len(rows)} prodotti...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_product, r[0], r[1], r[2], r[3]) for r in rows]
        done_count = 0
        for future in concurrent.futures.as_completed(futures):
            done_count += 1
            if done_count % 10 == 0 or done_count == len(rows):
                print(f"📈 Progressi: {done_count}/{len(rows)}")

    print(f"🏁 Download completato! Controlla la cartella {BASE_DIR}")

if __name__ == "__main__":
    main()
