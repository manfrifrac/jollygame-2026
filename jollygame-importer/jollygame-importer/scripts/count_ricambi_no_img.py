import json

def run():
    with open('master_sync_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_ricambi_skus = set()
    ricambi_no_image = set()
    
    for p in data:
        for r in p['ricambi']:
            all_ricambi_skus.add(r['sku'])
            if not r['images'] or r['images'] == '[]':
                ricambi_no_image.add(r['sku'])
                
    print(f"Totale SKU ricambi unici nei prodotti sync: {len(all_ricambi_skus)}")
    print(f"Di cui SENZA immagine nel DB: {len(ricambi_no_image)}")
    print(f"Esempi senza immagine: {list(ricambi_no_image)[:10]}")

if __name__ == "__main__":
    run()
