import csv
import os

RENAME_MAP = {
    "Spa Idromassaggio Intex": "Idromassaggio Intex PureSpa",
    "Idromassaggio Intex Spa": "Idromassaggio Intex PureSpa",
    "Idromassaggio Gonfiabile Lay-Z-Spa": "Idromassaggio Bestway Lay-Z-Spa",
    "Idromassaggio Gonfiabile Bestway": "Idromassaggio Bestway Lay-Z-Spa",
    "Filtro a Cartuccia Bestway": "Sistemi di Filtrazione a Cartuccia Bestway",
    "Filtro A Sabbia Bestway": "Sistemi di Filtrazione a Sabbia Bestway",
    "Telo Termico Intex per Piscine Rettangolari": "Telo di Copertura Termico Intex",
    "Telo Termico Intex": "Telo di Copertura Termico Intex",
    "Erba Sintetica Lite": "Erba Sintetica Bestway",
}

def rename_masters(file_path):
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            m = row['Master_Title']
            if m in RENAME_MAP:
                row['Master_Title'] = RENAME_MAP[m]
            rows.append(row)
            
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

rename_masters("gold_consolidated_final.csv")
print("✅ Nomi Master normalizzati per eliminare gli ultimi duplicati.")
