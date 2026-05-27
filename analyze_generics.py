import csv
import os

def analyze_cheap_accessories(file_path):
    if not os.path.exists(file_path):
        return
    
    branded = []
    generic = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                price = float(row['Prezzo'])
                if price >= 25:
                    continue
            except:
                continue
                
            title = row['Titolo'].lower()
            original_title = row['Titolo']
            
            # Check if it mentions Bestway specific lines or just generic terms
            if 'bestway' in title or 'flowclear' in title or 'lay-z-spa' in title or 'tipo i' in title or 'tipo ii' in title or 'tipo iii' in title or 'tipo vi' in title or 'size' in title:
                branded.append(original_title)
            else:
                generic.append(original_title)

    print(f"--- ANALISI ACCESSORI ECONOMICI (<25€) in {file_path} ---")
    print(f"Totale analizzati: {len(branded) + len(generic)}")
    print(f"Specifici del Brand (es. cartucce per loro pompe): {len(branded)}")
    print(f"Potenzialmente Generici (es. termometri, toppe): {len(generic)}\n")
    
    print("Esempi Specifici (Solo per Bestway):")
    for t in branded[:5]: print(f"  - {t}")
        
    print("\nEsempi Generici (Vanno bene per tutte le piscine):")
    for t in generic[:5]: print(f"  - {t}")

analyze_cheap_accessories("gold_bestway_final.csv")
