import csv
import json
from collections import defaultdict

def full_catalog_analysis(files):
    report = {}
    for f in files:
        brand = f.split('_')[1].capitalize()
        stats = {
            "total": 0,
            "price_tiers": {"<50": 0, "50-200": 0, "200-500": 0, ">500": 0},
            "core_functions": defaultdict(int)
        }
        
        with open(f, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                stats["total"] += 1
                try:
                    p = float(row['Prezzo'])
                    if p < 50: stats["price_tiers"]["<50"] += 1
                    elif p < 200: stats["price_tiers"]["50-200"] += 1
                    elif p < 500: stats["price_tiers"]["200-500"] += 1
                    else: stats["price_tiers"][">500"] += 1
                except: pass
                
                tags = row['Tags'].lower()
                if 'piscine' in tags: stats["core_functions"]["Piscine/SPA"] += 1
                elif 'filtraggio' in tags or 'pompe' in tags: stats["core_functions"]["Filtrazione/Pompe"] += 1
                elif 'pulitori' in tags: stats["core_functions"]["Pulizia/Robot"] += 1
                elif 'coperture' in tags: stats["core_functions"]["Coperture/Teli"] += 1
                else: stats["core_functions"]["Accessori Tecnici"] += 1
        
        report[brand] = stats
    return report

analysis = full_catalog_analysis(["gold_intex_final.csv", "gold_bestway_final.csv", "gold_fluidra_final.csv"])
print(json.dumps(analysis, indent=2))
