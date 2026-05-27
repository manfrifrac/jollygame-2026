import pandas as pd
import json
import re

def analyze_gre_catalog():
    # 1. Load Excel Listino
    excel_file = 'LISTINOMANUFACTURASGRE2026.xlsx'
    df = pd.read_excel(excel_file)
    
    # Mapping based on previous inspection:
    # 2: Parent Category
    # 3: Sub Category
    # 6: SKU
    # 7: Title
    # 9: EAN
    # 15: Price
    
    excel_data = []
    for _, row in df.iterrows():
        sku = str(row.iloc[6]).strip().upper() if pd.notna(row.iloc[6]) else None
        if sku and sku != 'NAN' and sku != 'REF' and len(sku) > 2:
            excel_data.append({
                "sku": sku,
                "ean": str(row.iloc[9]).strip() if pd.notna(row.iloc[9]) else "",
                "title": str(row.iloc[7]).strip(),
                "cat_parent": str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else "Unknown",
                "cat_sub": str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else "Unknown",
                "price": row.iloc[15] if pd.notna(row.iloc[15]) else 0
            })

    # 2. Group by Typology
    typologies = {}
    for item in excel_data:
        t = item['cat_parent']
        if t not in typologies: typologies[t] = []
        typologies[t].append(item)
        
    print(f"Total Gre products in Listino: {len(excel_data)}")
    print("Typologies found in Excel:")
    for t, items in typologies.items():
        print(f"  - {t}: {len(items)} items")

    # 3. Analyze Attributes for Variant Selection
    # Example for Pools: Model Name, Shape, Dimensions
    # Example for Covers: Model of Pool, Type (Summer/Winter), Dimensions
    
    analysis = {}
    for t, items in typologies.items():
        analysis[t] = {
            "total_items": len(items),
            "common_attributes": [],
            "example_items": items[:3]
        }
        
        # Suggest attributes based on category
        if "Piscine" in t:
            analysis[t]["suggested_selectors"] = ["Forma (Ovale/Tonda/Rettangolare)", "Materiale (Legno/Acciaio/Composito)", "Dimensioni", "Finitura (Bianca/Antracite/Legno)"]
        elif "Coperture" in t or "Liner" in t:
            analysis[t]["suggested_selectors"] = ["Modello Piscina Compatibile", "Dimensioni", "Spessore (per Liner)", "Materiale"]
        else:
            analysis[t]["suggested_selectors"] = ["Modello/Serie", "Caratteristica Tecnica (Potenza/Capacità)"]

    # 4. Load Shopify Data for Comparison
    with open('shopify_gre_full_data.json', 'r') as f:
        shopify_data = json.load(f)
        
    # Check for image discrepancies (e.g., generic images used)
    # A common problem is many variants sharing the same image
    discrepancies = []
    for p in shopify_data:
        images_used = set()
        for v in p['variants']:
            if v['image']: images_used.add(v['image'])
        
        if len(p['variants']) > 1 and len(images_used) == 1:
            discrepancies.append({
                "title": p['title'],
                "variant_count": len(p['variants']),
                "shared_image": list(images_used)[0]
            })

    report = {
        "typologies": analysis,
        "shopify_image_discrepancies": discrepancies,
        "total_shopify_gre": len(shopify_data)
    }
    
    with open('gre_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=4)
    print("\nAnalysis report generated: gre_analysis_report.json")

if __name__ == "__main__":
    analyze_gre_catalog()
