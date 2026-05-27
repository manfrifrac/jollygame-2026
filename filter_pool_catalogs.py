import csv
import os

# Keywords that indicate a pool-related product
POOL_KEYWORDS = [
    'piscina', 'pool', 'filtro', 'pompa', 'cloro', 'skimmer', 'copertura', 
    'scaletta', 'liner', 'robot', 'pulitore', 'sabbia', 'cartuccia', 
    'riscaldamento', 'solare', 'doccia', 'bordo', 'tubo', 'raccordo',
    'valvola', 'kit', 'manutenzione', 'test', 'ph', 'cl', 'analisi',
    'aspiratore', 'spazzola', 'guadino', 'termometro', 'clorinatore',
    'elettrolisi', 'idromassaggio', 'spa', 'pure-spa', 'purespa', 'gonfiabile'
]

# Keywords that indicate we should EXCLUDE the product (too generic or unrelated)
EXCLUDE_KEYWORDS = [
    'kayak', 'canotto', 'canoa', 'materasso', 'materassino', 'camping', 
    'campeggio', 'tenda', 'sacco a pelo', 'poltrona', 'divano', 'giocattolo',
    'pallone', 'braccioli', 'ciambella', 'cavalcabile', 'isola', 'zattera',
    'surf', 'sup', 'paddle', 'remi', 'gonfiatore manuale'
]

def filter_pool_products(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Skipping {input_file}, not found.")
        return
    
    total = 0
    kept = 0
    excluded_by_type = 0
    excluded_no_match = 0
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        filtered_rows = []
        for row in reader:
            total += 1
            title = row['Titolo'].lower()
            desc = row['Descrizione_HTML'].lower()
            text = title + " " + desc
            
            # 1. Check if it contains exclusion keywords (Kayaks, camping, etc.)
            if any(k in title for k in EXCLUDE_KEYWORDS):
                excluded_by_type += 1
                continue
            
            # 2. Check if it contains inclusion keywords
            if any(k in text for k in POOL_KEYWORDS):
                filtered_rows.append(row)
                kept += 1
            else:
                excluded_no_match += 1
                
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_rows)
        
    print(f"--- FILTERING REPORT: {input_file} ---")
    print(f"Total processed: {total}")
    print(f"Kept (Pool related): {kept}")
    print(f"Excluded (Non-pool type): {excluded_by_type}")
    print(f"Excluded (No keywords match): {excluded_no_match}")
    print(f"Saved to: {output_file}\n")

# Run filtering
filter_pool_products("intex_export_shopify.csv", "intex_pools_only.csv")
filter_pool_products("bestway_export_shopify.csv", "bestway_pools_only.csv")
