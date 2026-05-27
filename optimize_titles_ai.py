import csv
import os
import time
import json
from groq import Groq
import dotenv

dotenv.load_dotenv(dotenv_path="jollygame-importer/jollygame-importer/.env")

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Mapping categories to Shopify standards
CATEGORY_MAP = {
    "piscine fuori terra": "Categoria:Piscine",
    "piscine interrate": "Sottocategoria:Piscine interrate",
    "pompe di calore": "Sottocategoria:Pompe di calore",
    "pulitori elettrici": "Sottocategoria:Pulitori elettrico",
    "robot pulitori": "Categoria:Pulitori",
    "filtri": "Sottocategoria:Filtri",
    "trattamento acqua": "Categoria:Trattamento acqua",
    "coperture": "Categoria:Coperture",
    "accessori": "Categoria:Accessori"
}

def optimize_title(old_title, vendor):
    try:
        prompt = f"""Riscrivi il titolo di questo prodotto per un e-commerce di piscine (Shopify).
Prodotto Originale: {old_title}
Fornitore: {vendor}

Regole:
1. Usa il formato "Titolo Prodotto [Modello/Serie] [Specifiche principali]"
2. Rendi il titolo elegante e professionale (Capitalize Each Word).
3. Rimuovi codici interni inutili ma tieni lo SKU se fa parte del nome comune.
4. Lunghezza ideale: 50-70 caratteri.
5. Rispondi SOLO con il nuovo titolo, niente commenti.

Esempio: "POMPA FILTRO 2006 L/H" -> "Pompa Filtro Intex da 2.006 l/h"
"""
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return completion.choices[0].message.content.strip().replace('"', '')
    except Exception as e:
        print(f"Error optimizing {old_title}: {e}")
        return old_title

def process_file(input_file, output_file, vendor, limit=None):
    if not os.path.exists(input_file):
        return
    
    print(f"Processing {input_file}...")
    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = list(csv.DictReader(f))
        
        count = 0
        for row in reader:
            count += 1
            if limit and count > limit: break
            
            print(f"  [{count}/{len(reader)}] Optimizing: {row['Titolo']}")
            row['Titolo_Originale'] = row['Titolo']
            row['Titolo'] = optimize_title(row['Titolo'], vendor)
            
            # Taxonomy fix
            tags = row['Tags'].lower()
            new_tags = []
            for key, val in CATEGORY_MAP.items():
                if key in tags:
                    new_tags.append(val)
            
            # Default tags
            new_tags.append(f"Brand:{vendor}")
            if "ricambio" in tags: new_tags.append("Ricambio")
            
            row['Tags'] = ",".join(list(set(new_tags)))
            rows.append(row)
            
            # Sleep to avoid rate limits
            time.sleep(0.5)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if not rows: return
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved to {output_file}")

# Process files (using a limit for safety in this turn, or full if requested)
# For now I will do a sample of 20 each to show the quality
process_file("intex_pools_only.csv", "gold_intex_sample.csv", "Intex", limit=20)
process_file("bestway_pools_only.csv", "gold_bestway_sample.csv", "Bestway", limit=20)
process_file("fluidra_unique_import.csv", "gold_fluidra_sample.csv", "Fluidra", limit=20)
