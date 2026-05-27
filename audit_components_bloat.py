import csv
from collections import Counter

def audit_components():
    masters = Counter()
    with open('gold_consolidated_final.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not 'piscine' in row['Tags'].lower():
                masters[row['Master_Title']] += 1
                
    print("--- TOP 30 MASTER COMPONENTI (PER POTENZIALE AGGREGAZIONE) ---")
    for m, count in masters.most_common(30):
        print(f"  [{count}] {m}")

audit_components()
