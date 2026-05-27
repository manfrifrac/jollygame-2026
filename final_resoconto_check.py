import csv
import json
from collections import Counter, defaultdict

# agreed filters
SPARE_KEYWORDS = ['vite', 'bullone', 'guarnizione', 'tappo', 'raccordo', 'valvola', 'tubo', 'perno', 'molla', 'adattatore', 'connettore', 'staffa', 'supporto', 'piastra', 'vano skimmer']
LEISURE_KEYWORDS = ['cuffia', 'occhialini', 'maschera', 'boccaglio', 'snorkeling', 'pallone', 'gioco', 'beach ball', 'canestro', 'porta da calcio', 'giubbino salvataggio']
BABY_POOL_KEYWORDS = ['mini frame', 'small frame', 'piscina bambini', 'piscina baby', 'tre anelli', 'quattro anelli']

def final_simulated_report(file_path):
    final_masters = defaultdict(list)
    excluded_count = 0
    excluded_groups = Counter()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row['Titolo'].lower()
            master = row['Master_Title']
            price = float(row['Prezzo'])
            tags = row['Tags'].lower()
            
            exclude = False
            reason = ""
            
            # 1. Spare parts
            if any(k in title for k in SPARE_KEYWORDS):
                exclude = True
                reason = "Ricambi/Hardware"
            # 2. Leisure
            elif any(k in title for k in LEISURE_KEYWORDS):
                exclude = True
                reason = "Leisure/Nuoto"
            # 3. Baby Pools < 100
            elif any(k in title for k in BABY_POOL_KEYWORDS) and price < 100:
                exclude = True
                reason = "Piscine Baby/Low Value"
            # 4. Inflatable ring pools (Easy/Fast set) < 100
            elif ('easy set' in title or 'fast set' in title) and price < 100:
                exclude = True
                reason = "Piscine Gonfiabili Entry"
            # 5. Generic cheap items < 25 (unless consumables like cartridges)
            elif price < 25 and not 'cartucc' in title and not 'toppa' in title and not 'kit test' in title:
                exclude = True
                reason = "Accessori < 25€ (Non essenziali)"

            if exclude:
                excluded_count += 1
                excluded_groups[reason] += 1
            else:
                final_masters[master].append(row)

    # Report Stats
    master_list = []
    for master, variants in final_masters.items():
        v_prices = [float(v['Prezzo']) for v in variants]
        brand = "Intex" if 'brand:intex' in variants[0]['Tags'].lower() else "Bestway"
        if 'brand:fluidra' in variants[0]['Tags'].lower(): brand = "Fluidra"
        
        master_list.append({
            "name": master,
            "variants": len(variants),
            "min_price": min(v_prices),
            "max_price": max(v_prices),
            "brand": brand
        })

    return {
        "final_stats": {
            "total_master_products": len(final_masters),
            "total_variants": sum(len(v) for v in final_masters.values()),
            "total_excluded_items": excluded_count
        },
        "exclusion_details": dict(excluded_groups),
        "top_master_families": sorted(master_list, key=lambda x: x['variants'], reverse=True)[:15]
    }

res = final_simulated_report('gold_consolidated_final.csv')
print(json.dumps(res, indent=2))
