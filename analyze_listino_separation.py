import pandas as pd
import json
import re
from collections import defaultdict

def extract_variant_attributes(title):
    # Dimensions (e.g., 500x300, Ø 350)
    dims = re.findall(r'(\d+\s*[xX]\s*\d+|[oOØ\s]*\d+)', title)
    # Height
    h = re.findall(r'[hH]\s*(\d+)', title)
    # Shape
    shape = "Altro"
    if "OVAL" in title.upper(): shape = "Ovale"
    elif "TOND" in title.upper() or "ROTOND" in title.upper(): shape = "Tonda"
    elif "RETTANG" in title.upper(): shape = "Rettangolare"
    elif "QUADRAT" in title.upper(): shape = "Quadrata"
    
    return {
        "Misura": dims[0].strip() if dims else "Standard",
        "Altezza": f"{h[0]} cm" if h else "Standard",
        "Forma": shape
    }

def main():
    df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx')
    
    # Columns: 2: Macro, 3: Category, 4: SubCategory/Series, 6: SKU, 7: Title, 9: EAN, 15: Price
    groups = defaultdict(list)
    
    for _, row in df.iterrows():
        sku = str(row.iloc[6]).strip().upper()
        if sku and sku not in ['NAN', 'REF', 'ARTICOLO'] and len(sku) > 2:
            macro = str(row.iloc[2]).strip()
            cat = str(row.iloc[3]).strip()
            sub = str(row.iloc[4]).strip()
            
            # This is the "separation" the user refers to
            group_name = f"{macro} > {cat} > {sub}"
            groups[group_name].append({
                "sku": sku,
                "ean": str(row.iloc[9]).strip(),
                "title": str(row.iloc[7]).strip(),
                "price": row.iloc[15]
            })

    final_structure = {}
    for group_name, items in groups.items():
        # Title of the main product on Shopify
        parts = group_name.split(" > ")
        product_title = f"Gre - {parts[2]}"
        
        # Analyze what varies to create options
        has_multiple_shapes = len(set(extract_variant_attributes(i['title'])['Forma'] for i in items)) > 1
        has_multiple_dims = len(set(extract_variant_attributes(i['title'])['Misura'] for i in items)) > 1
        has_multiple_heights = len(set(extract_variant_attributes(i['title'])['Altezza'] for i in items)) > 1
        
        option_names = []
        if has_multiple_shapes: option_names.append("Forma")
        if has_multiple_dims: option_names.append("Dimensioni")
        if has_multiple_heights: option_names.append("Altezza")
        
        # Limit to 3 options
        option_names = option_names[:3]
        if not option_names and len(items) > 1:
            option_names = ["Modello"]

        variants = []
        for i in items:
            attr = extract_variant_attributes(i['title'])
            v_opts = []
            for opt_name in option_names:
                v_opts.append({"name": attr.get(opt_name, "Standard"), "optionName": opt_name})
            
            # If no options but multiple items, add a differentiator
            if not v_opts and len(items) > 1:
                v_opts.append({"name": i['title'][:50], "optionName": "Modello"})
            
            variants.append({
                "sku": i['sku'],
                "ean": i['ean'],
                "price": i['price'],
                "options": v_opts,
                "full_title": i['title']
            })
            
        final_structure[group_name] = {
            "shopify_title": product_title,
            "category": parts[1],
            "options": option_names if option_names else ["Tipologia"],
            "variants": variants
        }

    with open('gre_import_listino_structure.json', 'w', encoding='utf-8') as f:
        json.dump(final_structure, f, indent=4)
    
    print(f"Analisi completata. Creati {len(final_structure)} prodotti basati sulla separazione del listino.")
    
    # Example output for the user
    example_key = list(final_structure.keys())[2] # Steel pools nordic
    print(f"\nEsempio di separazione per '{example_key}':")
    print(f"Prodotto Shopify: {final_structure[example_key]['shopify_title']}")
    print(f"Opzioni Varianti: {final_structure[example_key]['options']}")
    print(f"Numero varianti: {len(final_structure[example_key]['variants'])}")

if __name__ == "__main__":
    main()
