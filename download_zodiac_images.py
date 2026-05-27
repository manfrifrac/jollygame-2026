import csv
import os
import requests
import re
import time
from urllib.parse import urlparse

def download_images():
    input_file = "zodiac_full_export.csv"
    output_dir = "zodiac_images"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(input_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row['Titolo'].replace("/", "-").replace(" ", "_")
            image_urls = row['Immagini'].split(";")
            
            if not image_urls or image_urls == ['']:
                continue
                
            product_dir = os.path.join(output_dir, title)
            if not os.path.exists(product_dir):
                os.makedirs(product_dir)
            
            print(f"\nScaricando immagini per: {row['Titolo']}")
            
            for i, url in enumerate(image_urls):
                if not url or "youtube" in url:
                    continue
                
                # Prova a forzare l'alta risoluzione (Original invece di Medium)
                high_res_url = url.replace("/Medium/", "/Original/").replace("Medium-", "Original-")
                
                # Ottieni estensione originale o usa .jpg
                ext = ".jpg"
                if ".png" in url.lower(): ext = ".png"
                elif ".webp" in url.lower(): ext = ".webp"
                
                filename = f"{title}_{i+1}{ext}"
                filepath = os.path.join(product_dir, filename)
                
                if os.path.exists(filepath):
                    continue

                try:
                    # Usiamo Mullvad proxy se lo script viene lanciato durante la sessione VPN
                    proxies = {
                        "http": "socks5h://10.64.0.1:1080",
                        "https": "socks5h://10.64.0.1:1080"
                    }
                    
                    # Proviamo prima l'alta risoluzione
                    try:
                        r = requests.get(high_res_url, timeout=10, proxies=proxies)
                        if r.status_code != 200:
                            r = requests.get(url, timeout=10, proxies=proxies)
                    except:
                        r = requests.get(url, timeout=10, proxies=proxies)

                    if r.status_code == 200:
                        with open(filepath, 'wb') as f_img:
                            f_img.write(r.content)
                        print(f"  [OK] Salvata: {filename}")
                        time.sleep(0.5) # Piccolo delay per non stressare il server
                    else:
                        print(f"  [ERR] Impossibile scaricare: {url} (Status: {r.status_code})")
                except Exception as e:
                    print(f"  [ERR] Errore su {url}: {e}")

if __name__ == "__main__":
    download_images()
