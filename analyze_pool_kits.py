import pandas as pd
import re
from collections import defaultdict

def extract_details(title):
    # Dimensions
    dims = re.findall(r'(\d+\s*[xX]\s*\d+|[oOØ\s]*\d+)', title)
    # Filter
    filtro = re.search(r'FILTRO A (SABBIA|CARTUCCIA|AQUALOON) DA (\d+m³/h|\d+)', title.upper())
    # Special equipment
    smart_plug = 'SMART PLUG' in title.upper()
    led = 'FARETTO' in title.upper() or 'LED' in title.upper()
    
    return {
        'dims': dims[0].strip() if dims else 'N/A',
        'filter': filtro.group(0) if filtro else 'N/A',
        'smart_plug': smart_plug,
        'led': led
    }

def main():
    df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx')
    
    # Analyze Steel Wall pools
    acciaio = df[df.iloc[:, 3].str.contains('acciaio', na=False, case=False)]
    
    model_size_groups = defaultdict(list)
    for _, row in acciaio.iterrows():
        title = row.iloc[7]
        sku = row.iloc[6]
        # Extract model
        match = re.search(r'(ATLANTIS|BORA BORA|FIDJI|MAURITIUS|PACIFIC|SICILIA|ISLANDA|NORDIC|KEA|KEOPS|MAGNOLIA|AMAZONIA|PROV|PR)', title.upper())
        model = match.group(1) if match else 'OTHER'
        
        # Also need color/decoration to be precise
        decor = 'BIANCA'
        for d in ['NORDIC', 'ANTRACITE', 'LEGNO', 'PIETRA', 'GRAFITE']:
            if d in title.upper():
                decor = d
                break
        
        details = extract_details(title)
        # Group by Model + Decor + Size
        key = f"{model} {decor} | {details['dims']}"
        model_size_groups[key].append((sku, title, details))

    print("--- ANALISI KIT MULTIPLI (STESSA PISCINA, DIVERSO EQUIPAGGIAMENTO) ---")
    
    for key, items in model_size_groups.items():
        if len(items) > 1:
            filters = set(i[2]['filter'] for i in items)
            plugs = set(i[2]['smart_plug'] for i in items)
            leds = set(i[2]['led'] for i in items)
            
            if len(filters) > 1 or len(plugs) > 1 or len(leds) > 1:
                print(f"\n📍 GRUPPO: {key}")
                for sku, title, det in items:
                    print(f"  SKU: {sku}")
                    print(f"    - Filtro: {det['filter']}")
                    print(f"    - SmartPlug: {'Sì' if det['smart_plug'] else 'No'}")
                    print(f"    - LED: {'Sì' if det['led'] else 'No'}")
                    # Briefly show why it might be different in title
                    print(f"    - Note: {title[:80]}...")

if __name__ == "__main__":
    main()
