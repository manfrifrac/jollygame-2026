import csv
from collections import defaultdict

def audit_tag_conflicts(file_path):
    conflicts = defaultdict(list)
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tags = [t.strip().lower() for t in row['Tags'].split(',')]
            
            # Identifico se il prodotto ha tag conflittuali
            has_piscina = 'categoria:piscine' in tags
            has_filtro = 'categoria:filtraggio' in tags
            has_accessori = 'categoria:accessori' in tags
            
            if has_piscina and (has_filtro or has_accessori):
                conflicts[row['Titolo']].append(tags)

    print(f"--- ANALISI CONFLITTI TAG (Prodotti con troppe categorie) ---")
    for title, tag_list in list(conflicts.items())[:20]:
        print(f"Prodotto: {title}")
        print(f"  Tags: {tag_list}")

audit_tag_conflicts('gold_consolidated_final.csv')
