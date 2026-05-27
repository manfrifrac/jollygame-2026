import csv
import os

# --- BLACKLIST DEFINITIVA ---
# Prodotti da eliminare assolutamente
STRICT_BLACKLIST = [
    'materasso', 'airbed', 'pillow rest', 'dura-beam', 'comfort-plush', 'downy', 'classic downy', # Materassi
    'cuffia', 'nuoto', 'occhialini', 'maschera', 'boccaglio', 'snorkeling', 'set snorkeling',     # Nuoto
    'pallone', 'gioco', 'beach ball', 'canestro', 'porta da calcio', 'frisbee',                   # Giochi
    'kayak', 'canotto', 'canoa', 'remi', 'giubbotto salvataggio',                                 # Nautica
    'tappeto elastico', 'scivolo', 'altalena', 'play center',                                     # Parchi gioco
    'camping', 'campeggio', 'sacco a pelo', 'tenda', 'fornello'                                   # Camping
]

# Parole che potrebbero essere nella blacklist ma che indicano prodotti da TENERE (Salvagente tecnico?)
# In realtà per ora meglio essere severi.

def hard_filter(file_path):
    if not os.path.exists(file_path):
        return
    
    rows_to_keep = []
    removed_count = 0
    removed_examples = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            title = (row.get('Titolo', '') or "").lower()
            original_title = row.get('Titolo', '')
            
            # Check against blacklist
            if any(k in title for k in STRICT_BLACKLIST):
                removed_count += 1
                if len(removed_examples) < 5:
                    removed_examples.append(original_title)
                continue
            
            rows_to_keep.append(row)
            
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_keep)
        
    print(f"--- HARD FILTER: {file_path} ---")
    print(f"  Prodotti Rimossi (Fuori Settore): {removed_count}")
    print(f"  Prodotti Rimasti (Piscine Tech): {len(rows_to_keep)}")
    if removed_examples:
        print(f"  Esempi rimossi: {', '.join(removed_examples)}...")

files = ["gold_consolidated_final.csv"] # Agiamo sul file già parzialmente lavorato
for f in files:
    hard_filter(f)
