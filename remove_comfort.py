import csv
import os

# Keywords that indicate "comfort" or "leisure" items to be removed
COMFORT_KEYWORDS = [
    'cuscino', 'poggiatesta', 'portabicchieri', 'doccia', 'solare', 'doccia solare',
    'supporto per bevande', 'vassoio'
]

def remove_comfort_items(file_path):
    if not os.path.exists(file_path):
        return
    
    rows_to_keep = []
    removed_count = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            title = (row.get('Titolo', '') or "").lower()
            
            # Remove if it contains comfort keywords
            if any(k in title for k in COMFORT_KEYWORDS):
                removed_count += 1
                continue
                
            rows_to_keep.append(row)
            
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_keep)
        
    print(f"--- RIMOZIONE COMFORT: {file_path} ---")
    print(f"  Rimossi: {removed_count}")
    print(f"  Rimasti: {len(rows_to_keep)}")

files = ["gold_intex_final.csv", "gold_bestway_final.csv", "gold_fluidra_final.csv"]
for f in files:
    remove_comfort_items(f)
