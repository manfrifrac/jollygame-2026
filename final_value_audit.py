import csv
import os
import json
from collections import Counter

def audit_final_value(file_path):
    if not os.path.exists(file_path):
        return None
    
    total = 0
    under_50 = 0
    over_500 = 0
    categories = Counter()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            try:
                price = float(row['Prezzo'])
                if price < 50: under_50 += 1
                if price > 500: over_500 += 1
            except: pass
            
            tags = row['Tags'].lower()
            if 'piscine' in tags: categories['Piscine Strutturali'] += 1
            elif 'pulitori' in tags: categories['Pulitori'] += 1
            elif 'filtraggio' in tags: categories['Sistemi di Filtrazione'] += 1
            else: categories['Accessori Tecnici'] += 1
            
    return {
        "file": file_path,
        "total": total,
        "under_50_euro": under_50,
        "over_500_euro": over_500,
        "categories": dict(categories)
    }

files = ["gold_intex_final.csv", "gold_bestway_final.csv", "gold_fluidra_final.csv"]
for f in files:
    print(json.dumps(audit_final_value(f), indent=2))
