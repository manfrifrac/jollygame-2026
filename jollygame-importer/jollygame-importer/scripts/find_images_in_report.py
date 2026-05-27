import pandas as pd
import json
import os

def find_images_in_report():
    dump_path = "master_catalog_dump.json"
    revision_path = "../../REPORT_REVISIONE_JOLLYGAME_2026.csv"
    
    if not os.path.exists(dump_path) or not os.path.exists(revision_path):
        print(f"File non trovati: dump={os.path.exists(dump_path)}, revision={os.path.exists(revision_path)}")
        return

    # Load Shopify
    with open(dump_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    # Load Revision Report (Semicolon separator)
    df = pd.read_csv(revision_path, sep=';')
    
    # Prepara mappa Titolo (parziale) -> URL Immagine
    # Molti nuovi prodotti hanno titoli simili alle descrizioni nel report
    image_map = []
    for _, row in df.iterrows():
        if pd.notna(row['URL_IMMAGINE']) and row['URL_IMMAGINE'] != "None":
            image_map.append({
                "title": str(row['TITOLO']).lower(),
                "sku": str(row['SKU']).strip().upper(),
                "url": row['URL_IMMAGINE']
            })

    missing = [p for p in catalog if p['mediaCount']['count'] == 0 and p.get('vendor') == 'Gre']
    print(f"🔍 Analisi di {len(missing)} prodotti Gre senza foto...")

    found = []
    for p in missing:
        p_title = p['title'].lower()
        
        # Safe SKU extraction
        first_variant = p.get('variants', {}).get('nodes', [{}])[0]
        p_sku = (first_variant.get('sku') or "").strip().upper()
        
        target_img = None
        
        # 1. Match per SKU
        if p_sku:
            match = next((m for m in image_map if m['sku'] == p_sku), None)
            if match:
                target_img = match['url']
        
        # 2. Match per Titolo parziale
        if not target_img:
            # Esempio: "MINT" contenuto in "KIT Piscina... Mint..."
            match = next((m for m in image_map if m['title'] in p_title or p_title in m['title']), None)
            if match:
                target_img = match['url']

        if target_img:
            found.append({
                "id": p['id'],
                "title": p['title'],
                "sku": p_sku,
                "image_url": target_img
            })

    print(f"✅ Trovate {len(found)} immagini nel report di revisione.")
    
    with open("gre_images_from_report.json", "w", encoding="utf-8") as f:
        json.dump(found, f, indent=2)

if __name__ == "__main__":
    find_images_in_report()
