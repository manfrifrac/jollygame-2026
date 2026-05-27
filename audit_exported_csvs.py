import csv
import json
import os

def audit_csv(file_path):
    if not os.path.exists(file_path):
        return None
    
    total = 0
    with_price = 0
    with_ean = 0
    with_images = 0
    ricambi = 0
    commercial = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            
            # Price check
            try:
                price = float(row['Prezzo'].replace(',', '.'))
                if price > 0:
                    with_price += 1
            except:
                pass
            
            # EAN check
            ean = row['EAN'].strip()
            if ean and ean.lower() != 'none' and len(ean) >= 8:
                with_ean += 1
                
            # Images check
            imgs = row['Immagini_JSON']
            if imgs and imgs != '[]' and len(imgs) > 10:
                with_images += 1
                
            # Spare parts vs Commercial
            tags = row['Tags'].lower()
            if 'ricambio' in tags or 'spare' in tags:
                ricambi += 1
            else:
                commercial += 1
                
    return {
        "file": file_path,
        "total": total,
        "commercial_units": commercial,
        "spare_parts": ricambi,
        "valid_price": with_price,
        "valid_ean": with_ean,
        "with_images": with_images,
        "ready_to_import": min(with_price, with_images) # Simple heuristic
    }

files = ["intex_export_shopify.csv", "bestway_export_shopify.csv", "fluidra_export_shopify.csv"]
reports = []
for f in files:
    res = audit_csv(f)
    if res:
        reports.append(res)

print(json.dumps(reports, indent=2))
