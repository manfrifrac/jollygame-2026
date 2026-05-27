import pandas as pd
import json

df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx', header=2)
# Prendi i primi 5 prodotti che non hanno articoli o EAN nulli
subset = df[df['ARTICOLO'].notna() & df['EAN'].notna()].head(10)

test_data = []
for _, row in subset.iterrows():
    test_data.append({
        "sku": str(row['ARTICOLO']),
        "ean": str(int(row['EAN'])) if pd.notna(row['EAN']) else None,
        "title": str(row['DESCRIZIONE'])
    })

print(json.dumps(test_data, indent=2))
