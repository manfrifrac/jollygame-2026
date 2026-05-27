import csv
import os

# Ultra-strict blacklist for non-finished products and minor accessories
ULTRA_STRICT_BLACKLIST = [
    'vite', 'bullone', 'guarnizione', 'tappo', 'raccordo', 'valvola', 'tubo', 
    'manopola', 'perno', 'molla', 'dado', 'rondella', 'adattatore', 'connettore',
    'staffa', 'supporto', 'piastra', 'kit riparazione', 'pezzo', 'componente',
    'o-ring', 'oring', 'boccola', 'cavo', 'spina', 'interruttore', 'toppa', 
    'patch', 'fun ballz', 'pallina', 'vano skimmer', 'v-mariposa', 'vibrovent',
    'cuffia', 'occhialini', 'maschera', 'boccaglio', 'snorkeling'
]

def final_pruning(file_path):
    if not os.path.exists(file_path):
        return
    
    rows_to_keep = []
    removed_count = 0
    removed_examples = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            title = (row.get('Master_Title', '') or "").lower()
            
            # 1. Remove Spare Parts and non-technical items
            if any(k in title for k in ULTRA_STRICT_BLACKLIST):
                # Double check to not remove big items like "Pompa Filtro" or "Valvola Selettrice" (if high value)
                # But user wants ONLY finished products now.
                removed_count += 1
                if len(removed_examples) < 10:
                    removed_examples.append(row.get('Master_Title'))
                continue
                
            rows_to_keep.append(row)
            
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_keep)
        
    print(f"--- PRUNING FINALE: {file_path} ---")
    print(f"  Prodotti Rimossi: {removed_count}")
    print(f"  Prodotti Rimasti: {len(rows_to_keep)}")
    if removed_examples:
        print(f"  Esempi rimossi: {', '.join(set(removed_examples))}")

final_pruning("gold_consolidated_final.csv")
