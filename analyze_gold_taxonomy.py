import csv
from collections import Counter
import os

def analyze_tags(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} non ancora pronto.")
        return
        
    categories = Counter()
    subcategories = Counter()
    brands = Counter()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tags = row['Tags'].split(',')
            for tag in tags:
                if tag.startswith('Categoria:'):
                    categories[tag.replace('Categoria:', '')] += 1
                elif tag.startswith('Sottocategoria:'):
                    subcategories[tag.replace('Sottocategoria:', '')] += 1
                elif tag.startswith('Brand:'):
                    brands[tag.replace('Brand:', '')] += 1
                    
    print(f"--- ANALISI TAG: {file_path} ---")
    print("\n📦 CATEGORIE:")
    for cat, count in categories.most_common():
        print(f"  - {cat}: {count}")
    
    print("\n🔧 SOTTOCATEGORIE:")
    for sub, count in subcategories.most_common():
        print(f"  - {sub}: {count}")
        
    print("\n🏷️ BRAND:")
    for brand, count in brands.most_common():
        print(f"  - {brand}: {count}")

analyze_tags("gold_intex_final.csv")
