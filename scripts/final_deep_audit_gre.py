import pandas as pd
import json
import os

def final_deep_audit():
    # 1. Load Excel Listino
    listino_path = "LISTINOMANUFACTURASGRE2026.xlsx"
    df_listino = pd.read_excel(listino_path, header=2)
    df_listino['SKU_CLEAN'] = df_listino['ARTICOLO'].astype(str).str.strip().str.upper()
    
    # 2. Load Shopify Data
    shopify_path = "jollygame-importer/jollygame-importer/master_catalog_dump.json"
    with open(shopify_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    # 3. Identify Consolidated Series
    consolidated = [p for p in catalog if "Piscina Gre Serie" in p['title']]
    
    print(f"🔍 AUDIT FINALE: {len(consolidated)} Serie Consolidate trovate.")
    
    report = []
    for p in consolidated:
        series_info = {
            "title": p['title'],
            "id": p['id'],
            "variants_count": len(p['variants']['nodes']),
            "images_count": p['mediaCount']['count'] if 'mediaCount' in p else 0,
            "variants": []
        }
        
        for v in p['variants']['nodes']:
            sku = (v.get('sku') or "").strip().upper()
            price = v.get('price')
            # Look up price in listino for comparison
            match = df_listino[df_listino['SKU_CLEAN'] == sku]
            expected_price = "N/A"
            if not match.empty:
                # Prezzo 2026 + 3%
                base = match.iloc[0]['PREZZO DI VENDITA CONSIGLIATO 2026']
                if pd.notna(base):
                    expected_price = f"{base * 1.03:.2f}"
            
            series_info['variants'].append({
                "sku": sku,
                "price": price,
                "expected": expected_price,
                "status": "OK" if str(price) == str(expected_price) else "DIFF"
            })
        report.append(series_info)

    # 4. Print Summary
    for r in report:
        print(f"\n📦 {r['title']}")
        print(f"   🖼️ Immagini: {r['images_count']}")
        print(f"   🔢 Varianti: {r['variants_count']}")
        for v in r['variants'][:5]: # Mostra prime 5
            print(f"     - SKU {v['sku']}: {v['price']}€ (Listino: {v['expected']}€) -> {v['status']}")
        if r['variants_count'] > 5:
            print(f"     ... ed altre {r['variants_count']-5} varianti.")

    # 5. Check for "Lost" Gre Products
    all_series_skus = set()
    for r in report:
        for v in r['variants']:
            all_series_skus.add(v['sku'])
            
    leftovers = [p for p in catalog if p.get('vendor') == 'Gre' and "Piscina Gre Serie" not in p['title'] and "KIT Piscina" in p['title']]
    if leftovers:
        print(f"\n⚠️ PRODOTTI GRE NON CONSOLIDATI (da controllare):")
        for l in leftovers:
            print(f" - {l['title']} (SKU: {l['variants']['nodes'][0].get('sku')})")

    # 6. Save final report
    with open("final_audit_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    final_deep_audit()
