import csv
import os

TOY_KEYWORDS = [
    'gioco', 'play center', 'gonfiabile', 'salvagente', 'materassino', 
    'cavalcabile', 'isola', 'canestro', 'pallone', 'braccioli', 'ciambella',
    'scivolo', 'animali gonfiabili', 'tappeto elastico', 'castello'
]
TOY_EXCLUSIONS = ['spa', 'idromassaggio', 'poltrona', 'divano', 'piscina', 'copertura', 'cuscino']

def remove_toys(file_path):
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
            
            is_toy = False
            if any(k in title for k in TOY_KEYWORDS):
                if not any(ex in title for ex in TOY_EXCLUSIONS):
                    is_toy = True
                    
            if is_toy:
                removed_count += 1
                removed_titles.append(row.get('Titolo', ''))
                continue
                
            rows_to_keep.append(row)
            
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_keep)
        
    print(f"--- RIMOZIONE GIOCATTOLI: {file_path} ---")
    print(f"  Rimosso Giocattoli: {removed_count}")
    print(f"  Rimasti (Core Business): {len(rows_to_keep)}")
    if removed_count > 0:
        print(f"  Esempi rimossi: {', '.join(removed_titles[:3])}...")

files = ["gold_intex_final.csv", "gold_bestway_final.csv"]
for f in files:
    remove_toys(f)
