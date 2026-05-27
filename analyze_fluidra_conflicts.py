import csv
import json
import os

def load_skus_and_eans(file_path):
    data = {"skus": set(), "eans": set()}
    if not os.path.exists(file_path):
        return data
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row.get('SKU', '').strip().upper()
            ean = row.get('EAN', '').strip()
            if sku: data["skus"].add(sku)
            if ean and ean.lower() != 'none' and len(ean) >= 8: data["eans"].add(ean)
    return data

# Load existing/processed data
zodiac = load_skus_and_eans("zodiac_enriched_data.csv")
laghetto = load_skus_and_eans("laghetto_full_export_enriched.csv")
intex = load_skus_and_eans("intex_export_shopify.csv")
bestway = load_skus_and_eans("bestway_export_shopify.csv")

# Combine all "already handled" or "to be handled" sources
existing_skus = zodiac["skus"] | laghetto["skus"] | intex["skus"] | bestway["skus"]
existing_eans = zodiac["eans"] | laghetto["eans"] | intex["eans"] | bestway["eans"]

# Analyze Fluidra Top 177
fluidra_file = "fluidra_export_shopify.csv"
conflicts = []
unique_fluidra = []

if os.path.exists(fluidra_file):
    with open(fluidra_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                price = float(row['Prezzo'].replace(',', '.'))
                if price <= 0: continue
            except:
                continue
                
            sku = row['SKU'].strip().upper()
            ean = row['EAN'].strip()
            title = row['Titolo']
            
            is_duplicate = False
            reason = ""
            
            if sku in existing_skus:
                is_duplicate = True
                reason = f"SKU Conflict ({sku})"
            elif ean in existing_eans:
                is_duplicate = True
                reason = f"EAN Conflict ({ean})"
                
            if is_duplicate:
                conflicts.append({"title": title, "sku": sku, "ean": ean, "reason": reason})
            else:
                unique_fluidra.append(row)

print(f"--- FLUIDRA ANALYSIS (177 Priced Products) ---")
print(f"Total Priced: {len(conflicts) + len(unique_fluidra)}")
print(f"Conflicts found: {len(conflicts)}")
print(f"Unique to Import: {len(unique_fluidra)}")

if conflicts:
    print("\n--- SAMPLE CONFLICTS ---")
    for c in conflicts[:5]:
        print(f"- {c['title']} | {c['reason']}")

# Save unique Fluidra to a new file for safe import
if unique_fluidra:
    with open("fluidra_unique_import.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=unique_fluidra[0].keys())
        writer.writeheader()
        writer.writerows(unique_fluidra)
    print(f"\nCreated fluidra_unique_import.csv with {len(unique_fluidra)} products.")
