import csv
import os

# Keywords that strongly suggest a spare part or minor component
SPARE_PART_KEYWORDS = [
    'ricambio', 'spare', 'vite', 'bullone', 'guarnizione', 'tappo', 
    'raccordo', 'valvola', 'tubo flessibile', 'manopola', 'perno', 
    'molla', 'dado', 'rondella', 'adattatore', 'connettore', 'staffa',
    'supporto', 'piastra', 'kit riparazione', 'pezzo', 'componente',
    'o-ring', 'oring', 'boccola', 'cavo', 'spina', 'interruttore'
]

# Keywords that strongly suggest a FINISHED product (to avoid false positives)
FINISHED_PRODUCT_KEYWORDS = [
    'piscina', 'idromassaggio', 'spa', 'pompa filtro', 'clorinatore', 
    'pulitore', 'robot', 'scaletta', 'skimmer deluxe', 'generatore ozono',
    'aspiratore', 'pompa di calore', 'doccia'
]

def bonify_catalog(file_path):
    if not os.path.exists(file_path):
        return
    
    rows_to_keep = []
    removed_chemicals = 0
    removed_spares = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            title = row['Titolo'].lower()
            tags = row['Tags'].lower()
            
            # 1. Remove Chemicals (as requested before)
            if any(k in tags for k in ['trattamento acqua', 'prodotti chimici', 'cloro', 'ph', 'sale']):
                removed_chemicals += 1
                continue
            
            # 2. Remove Spare Parts
            is_spare = False
            if 'ricambio' in tags:
                is_spare = True
            
            # Check title for spare part keywords
            if any(k in title for k in SPARE_PART_KEYWORDS):
                # But check if it's a false positive (a finished product containing a keyword)
                if not any(k in title for k in FINISHED_PRODUCT_KEYWORDS):
                    is_spare = True
            
            if is_spare:
                removed_spares += 1
                continue
                
            rows_to_keep.append(row)
            
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_keep)
        
    print(f"--- BONIFICA: {file_path} ---")
    print(f"  Rimosso Chimici: {removed_chemicals}")
    print(f"  Rimosso Ricambi: {removed_spares}")
    print(f"  Rimasti (Finiti): {len(rows_to_keep)}")

# Run for current ready files
if os.path.exists("gold_intex_final.csv"):
    bonify_catalog("gold_intex_final.csv")
