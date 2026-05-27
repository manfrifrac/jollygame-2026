import csv
import json
from collections import Counter, defaultdict

def audit_consolidated(file_path):
    master_data = defaultdict(list)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            master_data[row['Master_Title']].append(row)
            
    total_masters = len(master_data)
    price_distribution = {"<50€": 0, "50-200€": 0, "200-500€": 0, ">500€": 0}
    category_distribution = Counter()
    brand_distribution = Counter()
    
    for master, variants in master_data.items():
        # Use the lowest price of variants as master price indicator
        min_price = min(float(v['Prezzo']) for v in variants)
        
        if min_price < 50: price_distribution["<50€"] += 1
        elif min_price < 200: price_distribution["50-200€"] += 1
        elif min_price < 500: price_distribution["200-500€"] += 1
        else: price_distribution[">500€"] += 1
        
        # Tags from first variant (usually consistent)
        tags = variants[0]['Tags'].lower()
        if 'brand:intex' in tags: brand_distribution['Intex'] += 1
        elif 'brand:bestway' in tags: brand_distribution['Bestway'] += 1
        elif 'brand:fluidra' in tags: brand_distribution['Fluidra'] += 1
        
        if 'piscine' in tags: category_distribution['Piscine/SPA'] += 1
        elif 'filtraggio' in tags or 'pompe' in tags: category_distribution['Filtrazione/Pompe'] += 1
        elif 'pulitori' in tags: category_distribution['Pulizia/Robot'] += 1
        elif 'coperture' in tags: category_distribution['Coperture/Teli'] += 1
        else: category_distribution['Accessori e Ricambi Tecnici'] += 1

    return {
        "total_master_products": total_masters,
        "price_tiers": price_distribution,
        "categories": dict(category_distribution),
        "brands": dict(brand_distribution)
    }

report = audit_consolidated('gold_consolidated_final.csv')
print(json.dumps(report, indent=2))
