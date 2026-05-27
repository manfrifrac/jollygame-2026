import csv
import os
import requests
import re
import time
from urllib.parse import urlparse

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename).replace(" ", "_").replace("/", "-")

def download_images():
    input_file = "laghetto_full_export_enriched.csv"
    output_dir = "laghetto_images"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(input_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_title = row['Titolo'] or "Prodotto_Senza_Nome"
            title = sanitize_filename(raw_title)
            image_urls = [u for u in row['Immagini'].split(";") if u.strip()]
            
            if not image_urls:
                continue
                
            product_dir = os.path.join(output_dir, title)
            if not os.path.exists(product_dir):
                os.makedirs(product_dir)
            
            print(f"\nScaricando immagini per: {raw_title}")
            
            for i, url in enumerate(image_urls):
                if not url or "youtube" in url or "data:image" in url:
                    continue
                
                # Get extension from URL
                parsed = urlparse(url)
                ext = os.path.splitext(parsed.path)[1]
                if not ext:
                    ext = ".webp" if ".webp" in url.lower() else ".jpg"
                
                filename = f"{title}_{i+1}{ext}"
                filepath = os.path.join(product_dir, filename)
                
                if os.path.exists(filepath):
                    print(f"  [SKIP] Già esistente: {filename}")
                    continue

                try:
                    r = requests.get(url, timeout=20, headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    })

                    if r.status_code == 200:
                        with open(filepath, 'wb') as f_img:
                            f_img.write(r.content)
                        print(f"  [OK] Salvata: {filename}")
                        time.sleep(0.3) # Avoid hitting server too hard
                    else:
                        print(f"  [ERR] Impossibile scaricare: {url} (Status: {r.status_code})")
                except Exception as e:
                    print(f"  [ERR] Errore su {url}: {e}")

if __name__ == "__main__":
    download_images()
