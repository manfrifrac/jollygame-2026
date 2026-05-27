import csv
from collections import Counter

def count_complex():
    master_counts = Counter()
    total_variants = 0
    
    with open('gold_consolidated_final.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            master_counts[row['Master_Title']] += 1
            total_variants += 1
            
    print(f"--- ANALISI POST-CONSOLIDAMENTO ---")
    print(f"Prodotti Master (quelli che vedrà il cliente): {len(master_counts)}")
    print(f"Varianti Totali: {total_variants}")
    print(f"Media Varianti per Prodotto: {total_variants/len(master_counts):.1f}")
    
    print("\nEsempi di prodotti con più varianti:")
    for master, count in master_counts.most_common(5):
        print(f"  - {master}: {count} varianti")

count_complex()
