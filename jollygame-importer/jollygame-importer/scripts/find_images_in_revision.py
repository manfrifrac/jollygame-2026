import pandas as pd
import json
import os

def find_images_in_revision():
    shopify_path = "master_catalog_dump.json"
    revision_path = "../../REPORT_REVISIONE_JOLLYGAME_2026.csv"
    
    if not os.path.exists(shopify_path) or not os.path.exists(revision_path):
        print(f"File non trovati: shopify={os.path.exists(shopify_path)}, revision={os.path.exists(revision_path)}")
        return

    # Load Shopify
    with open(shopify_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    # Load Revision
    df = pd.read_csv(revision_path, sep=';')
    # Filter rows with images
    df_images = df[df['URL_IMMAGINE'].notna() & (df['URL_IMMAGINE'] != "None")]
    
    # Create map SKU -> Image
    rev_map = {}
    for _, row in df_images.iterrows():
        sku = str(row['SKU']).strip().upper()
        rev_map[sku] = row['URL_IMMAGINE']

    missing = [p for p in catalog if p['mediaCount']['count'] == 0]
    print(f"🔍 Analisi di {len(missing)} prodotti senza foto...")

    found = []
    for p in missing:
        # Check first variant SKU
        sku = (p['variants']['nodes'][0].get('sku') or "").strip().upper()
        if sku in rev_map:
            found.append({
                "id": p['id'],
                "sku": sku,
                "title": p['title'],
                "image_url": rev_map[sku]
            })

    print(f"✅ Trovate {len(found)} immagini nel report di revisione.")
    
    with open("jollygame-importer/jollygame-importer/images_to_upload.json", "w", encoding="utf-8") as f:
        json.dump(found, f, indent=2)

if __name__ == "__main__":
    find_images_in_revision()
