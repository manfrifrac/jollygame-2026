import pandas as pd
import json
import re
from collections import defaultdict

def extract_pool_details(title):
    # Dimensions
    dims = re.findall(r'(\d+\s*[xX]\s*\d+|[oOØ\s]*\d+)', title)
    dim = dims[0].strip() if dims else 'Unica'
    
    # Structure
    structure = 'Rinforzi laterali'
    if 'OMEGA' in title.upper(): structure = 'Sistema Omega (senza gambe)'
    elif 'INTERRATA' in title.upper(): structure = 'Interrata'
    
    # Equipment/Kit
    kit = 'Standard + Filtro Sabbia'
    if 'AQUALOON' in title.upper(): kit = 'Filtro Aqualoon'
    if 'MOTORIZ' in title.upper(): kit = 'Skimmer Motorizzato'
    if 'SMART PLUG' in title.upper(): kit += ' + Smart Plug'
    
    # Decoration
    decor = 'Bianca'
    for d in ['NORDIC', 'ANTRACITE', 'LEGNO', 'PIETRA', 'GRAFITE']:
        if d in title.upper():
            decor = d.capitalize()
            break
            
    return {"Dim": dim, "Struttura": structure, "Kit": kit, "Decor": decor}

def main():
    with open('listino_master_map.json', 'r', encoding='utf-8') as f:
        listino = json.load(f)

    # RE-GROUPING LOGIC (The "Definitive" way)
    # We group by Subcategory + Main Model Name + Decoration
    groups = defaultdict(list)
    for sku, info in listino.items():
        title = info['title']
        subcat = info['subcategory']
        
        # Determine Main Product Name
        if 'Piscine' in subcat:
            details = extract_pool_details(title)
            # For pools, we group by Category + Decoration
            # Example: "Gre - Piscine in acciaio (Antracite)"
            prod_name = f"Gre - {subcat} ({details['Decor']})"
            groups[prod_name].append((sku, info, details))
        elif 'Liner' in subcat or 'Coperture' in subcat:
            # Group by Subcat + Base Name
            t_clean = title.upper().replace('COPERTURA ', '').replace('COP.', '').split(' PER ')[0]
            name = t_clean.split()[0]
            prod_name = f"Gre - {subcat} ({name})"
            groups[prod_name].append((sku, info, None))
        else:
            # Other accessories: group by first 2 words of subcat + first word of title
            name = title.split()[0].upper()
            prod_name = f"Gre - {subcat} ({name})"
            groups[prod_name].append((sku, info, None))

    # 1. GENERATE WORKFLOW CSV
    csv_rows = []
    for g_name, items in groups.items():
        for sku, info, det in items:
            row = {
                "Prodotto_Shopify": g_name,
                "Categoria": info['subcategory'],
                "SKU": sku,
                "EAN": info['ean'],
                "Prezzo": info['price'],
                "Titolo_Originale": info['title']
            }
            if det:
                row["Opzione_1_Dimensioni"] = det["Dim"]
                row["Opzione_2_Struttura"] = det["Struttura"]
                row["Opzione_3_Kit"] = det["Kit"]
            else:
                # Generic auto-detection for non-pool variants
                row["Opzione_1"] = info['title'][-40:] # Temporary
            csv_rows.append(row)
            
    df = pd.DataFrame(csv_rows)
    df.to_csv('LAVORO_STRUTTURA_GRE_2026.csv', index=False, encoding='utf-8-sig')

    # 2. GENERATE DESCRIPTIVE DOCUMENT (Markdown/Doc structure)
    doc_content = "# 📘 MANUALE DI RISTRUTTURAZIONE CATALOGO GRE 2026\n\n"
    doc_content += f"Questo documento descrive la nuova suddivisione di **{len(df)} SKU** in **{len(groups)} prodotti** su Shopify.\n\n"
    
    # Summarize by Macro-Category
    macro_groups = defaultdict(list)
    for g_name in groups:
        # Simple split to find parent
        parent = g_name.split(' (')[0]
        macro_groups[parent].append(g_name)
        
    for macro, sub_prods in macro_groups.items():
        doc_content += f"## 📁 {macro}\n"
        doc_content += f"In questa categoria abbiamo creato **{len(sub_prods)} prodotti**.\n\n"
        for sp in sub_prods[:10]:
            count = len(groups[sp])
            doc_content += f"*   **{sp}**: raggruppa **{count} varianti**.\n"
            if "Piscine" in macro:
                doc_content += "    *   *Selettori:* Dimensioni | Struttura | Equipaggiamento (Kit)\n"
            else:
                doc_content += "    *   *Selettori:* Modello / Misura specifica\n"
        if len(sub_prods) > 10: doc_content += f"*   ... e altri {len(sub_prods)-10} prodotti.\n"
        doc_content += "\n"

    with open('DESCRIZIONE_STRUTTURA_GRE.md', 'w', encoding='utf-8') as f:
        f.write(doc_content)

    print(f"Report generati: LAVORO_STRUTTURA_GRE_2026.csv e DESCRIZIONE_STRUTTURA_GRE.md")

if __name__ == "__main__":
    main()
