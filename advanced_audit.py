import csv
import os
import json
from collections import Counter

PRICE_BINS = [25, 100, 500]
TOY_KEYWORDS = ['gioco', 'play center', 'gonfiabile', 'salvagente', 'materassino', 'cavalcabile', 'isola', 'canestro', 'pallone', 'braccioli', 'ciambella']
TOY_EXCLUSIONS = ['spa', 'idromassaggio', 'poltrona', 'divano']

ACCESSORY_SUBCATEGORIES = {
    "Illuminazione": ['luce', 'led', 'faro'],
    "Manutenzione": ['spazzola', 'retino', 'guadino', 'aspiratore', 'manico', 'kit pulizia', 'termometro'],
    "Componenti Filtrazione": ['cartuccia', 'sfere filtranti', 'pompa', 'skimmer'],
    "Teli e Coperture": ['telo', 'copertura', 'termico', 'solare'],
    "Scalette e Sicurezza": ['scaletta', 'allarme'],
    "Altro": ['toppa', 'patch', 'piastra', 'tappeto', 'doccia']
}

def detailed_audit(file_path):
    if not os.path.exists(file_path):
        return None

    price_distribution = {f"< {PRICE_BINS[0]}": 0}
    for i in range(len(PRICE_BINS) - 1):
        price_distribution[f"{PRICE_BINS[i]}-{PRICE_BINS[i+1]}"] = 0
    price_distribution[f"> {PRICE_BINS[-1]}"] = 0
    
    toy_count = 0
    main_categories = Counter()
    accessory_breakdown = Counter()

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row['Titolo'].lower()
            tags = row['Tags'].lower()
            
            try:
                price = float(row['Prezzo'])
                if price < PRICE_BINS[0]:
                    price_distribution[f"< {PRICE_BINS[0]}"] += 1
                elif price > PRICE_BINS[-1]:
                    price_distribution[f"> {PRICE_BINS[-1]}"] += 1
                else:
                    for i in range(len(PRICE_BINS) - 1):
                        if PRICE_BINS[i] <= price < PRICE_BINS[i+1]:
                            price_distribution[f"{PRICE_BINS[i]}-{PRICE_BINS[i+1]}"] += 1
                            break
            except:
                pass

            is_toy = False
            if any(k in title for k in TOY_KEYWORDS):
                if not any(ex in title for ex in TOY_EXCLUSIONS):
                    is_toy = True
            if is_toy:
                toy_count += 1
            
            if 'categoria:piscine' in tags:
                main_categories['Piscine'] += 1
            elif 'categoria:pulitori' in tags:
                main_categories['Pulitori e Robot'] += 1
            elif 'categoria:filtraggio' in tags:
                 main_categories['Sistemi di Filtraggio'] += 1
            elif 'categoria:accessori' in tags:
                main_categories['Accessori Vari'] += 1
                found_subcat = False
                for subcat, keywords in ACCESSORY_SUBCATEGORIES.items():
                    if any(k in title for k in keywords):
                        accessory_breakdown[subcat] += 1
                        found_subcat = True
                        break
                if not found_subcat and is_toy:
                    accessory_breakdown['Giochi e Gonfiabili'] += 1
                elif not found_subcat:
                    accessory_breakdown['Componenti e Altro'] += 1
            else:
                 main_categories['Non Categorizzato'] += 1

    return {
        "file": file_path,
        "total_products": sum(main_categories.values()),
        "price_distribution": price_distribution,
        "potential_toys": toy_count,
        "main_categories": dict(main_categories),
        "accessory_details": dict(accessory_breakdown)
    }

report_intex = detailed_audit("gold_intex_final.csv")
report_bestway = detailed_audit("gold_bestway_final.csv")

print("--- AUDIT QUALITA' E VALORE ---")
if report_intex:
    print("--- FORNITORE: INTEX ---")
    print(json.dumps(report_intex, indent=2, ensure_ascii=False))
if report_bestway:
    print("--- FORNITORE: BESTWAY ---")
    print(json.dumps(report_bestway, indent=2, ensure_ascii=False))
