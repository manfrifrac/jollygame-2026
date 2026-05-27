import csv
import re
from collections import defaultdict
import json

def extract_dimensions(title):
    # Cerca pattern tipo 412x201x122 o 457x107 o 12' x 30"
    match = re.search(r'(\d+\s*[xX*]\s*\d+(?:\s*[xX*]\s*\d+)?)', title)
    if match:
        return match.group(1).replace(' ', '').lower()
    return "Standard"

def extract_kit(title):
    title_low = title.lower()
    if 'pompa' in title_low or 'filtro' in title_low:
        if 'sabbia' in title_low: return "Kit Filtro a Sabbia"
        return "Kit Pompa Filtro"
    if 'combo' in title_low: return "Kit Combo (Pompa + Cloro)"
    return "Solo Vasca / Base"

def consolidate_catalog(files):
    total_items = 0
    consolidated = defaultdict(lambda: defaultdict(list))
    
    for f in files:
        brand = f.split('_')[1].capitalize()
        with open(f, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                total_items += 1
                title = row['Titolo']
                
                # Rimuovi dimensioni e kit dal titolo per trovare il "Modello Base"
                base_model = title
                # Rimuovi dimensioni tipo 400x200x100
                base_model = re.sub(r'\d+\s*[xX*]\s*\d+(?:\s*[xX*]\s*\d+)?', '', base_model)
                # Rimuovi riferimenti a kit
                base_model = re.sub(r'(?i)con pompa|con filtro|kit|solo vasca|pompa a sabbia|filtro a sabbia', '', base_model)
                # Pulizia finale
                base_model = base_model.replace(' - ', ' ').replace(',', '').strip()
                base_model = re.sub(r'\s+', ' ', base_model)
                
                dim = extract_dimensions(title)
                kit = extract_kit(title)
                
                consolidated[brand][base_model].append({
                    "sku": row['SKU'],
                    "price": row['Prezzo'],
                    "dim": dim,
                    "kit": kit,
                    "original_title": title
                })
                
    # Statistiche
    report = []
    for brand, models in consolidated.items():
        report.append({
            "brand": brand,
            "master_products": len(models),
            "total_variants": sum(len(v) for v in models.values())
        })
        
    return report, consolidated

analysis, raw_data = consolidate_catalog(["gold_intex_final.csv", "gold_bestway_final.csv", "gold_fluidra_final.csv"])

print("--- REPORT ACCORPAMENTO VARIANTI ---")
print(json.dumps(analysis, indent=2))

# Mostra un esempio di prodotto con varianti
print("\n--- ESEMPIO DI ACCORPAMENTO (BESTWAY) ---")
example_brand = "Bestway"
example_model = list(raw_data[example_brand].keys())[0]
print(f"Prodotto Master: {example_model}")
for v in raw_data[example_brand][example_model][:5]:
    print(f"  -> Variante: [Dim: {v['dim']}, Kit: {v['kit']}] - SKU: {v['sku']} - Prezzo: €{v['price']}")
