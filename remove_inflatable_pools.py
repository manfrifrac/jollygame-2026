import csv
import os

# Keywords that indicate a cheap inflatable pool
INFLATABLE_POOL_KEYWORDS = [
    'piscina gonfiabile', 'fast set', 'easy set', 'piscina anello gonfiabile'
]

# We want to make sure we DO NOT remove SPAs, which are technically inflatable but high value
SPA_KEYWORDS = ['spa', 'idromassaggio', 'purespa', 'lay-z-spa', 'pure spa']

def remove_inflatable_pools(file_path):
    if not os.path.exists(file_path):
        return
    
    rows_to_keep = []
    removed_count = 0
    removed_titles = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            title = (row.get('Titolo', '') or "").lower()
            
            is_inflatable_pool = False
            
            if any(k in title for k in INFLATABLE_POOL_KEYWORDS):
                # If it's a SPA, it's not a cheap inflatable pool, so we keep it
                if not any(spa_k in title for spa_k in SPA_KEYWORDS):
                    is_inflatable_pool = True
                    
            if is_inflatable_pool:
                removed_count += 1
                removed_titles.append(row.get('Titolo', ''))
                continue
                
            rows_to_keep.append(row)
            
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_keep)
        
    print(f"--- RIMOZIONE PISCINE GONFIABILI: {file_path} ---")
    print(f"  Rimosse: {removed_count}")
    print(f"  Rimasti nel file: {len(rows_to_keep)}")
    if removed_count > 0:
        print(f"  Esempi: {', '.join(removed_titles[:3])}")

files = ["gold_intex_final.csv", "gold_bestway_final.csv"]
for f in files:
    remove_inflatable_pools(f)
