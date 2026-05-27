import csv
import os

def remove_chemicals(file_path):
    if not os.path.exists(file_path):
        return
    
    rows_to_keep = []
    removed_count = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            tags = row['Tags'].lower()
            # Keywords to exclude
            if 'trattamento acqua' in tags or 'prodotti chimici' in tags or 'cloro' in tags or 'ph' in tags or 'sale' in tags:
                removed_count += 1
                continue
            rows_to_keep.append(row)
            
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_keep)
        
    print(f"File {file_path}: Rimosso {removed_count} prodotti chimici. Rimasti {len(rows_to_keep)}.")

# We apply this to any "gold" file found
for f in os.listdir("."):
    if f.startswith("gold_") and f.endswith(".csv"):
        remove_chemicals(f)
