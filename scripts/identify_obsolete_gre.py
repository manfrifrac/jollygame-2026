import json
import os

def identify_obsolete_gre():
    report_path = "gre_price_update_report.json"
    dump_path = "jollygame-importer/jollygame-importer/master_catalog_dump.json"
    
    if not os.path.exists(report_path) or not os.path.exists(dump_path):
        print("File non trovati.")
        return

    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    with open(dump_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    # 70 SKUs on shopify but not in listino
    obsolete_skus = set([x['sku'].strip().upper() for x in report['on_shopify_not_in_listino']])
    
    to_draft = []
    for p in catalog:
        # Only draft Gre products
        if p.get('vendor') != 'Gre': continue
        
        # Check if all variants are obsolete (to draft the product)
        has_current_variant = False
        p_skus = []
        for v in p['variants']['nodes']:
            sku = (v.get('sku') or "").strip().upper()
            p_skus.append(sku)
            if sku and sku not in obsolete_skus:
                has_current_variant = True
        
        if not has_current_variant and p_skus:
            to_draft.append({
                "id": p['id'],
                "title": p['title'],
                "skus": p_skus
            })

    with open("gre_obsolete_to_draft.json", "w", encoding="utf-8") as f:
        json.dump(to_draft, f, indent=2)

    print(f"✅ Identificati {len(to_draft)} prodotti Gre obsoleti da spostare in BOZZA.")

if __name__ == "__main__":
    identify_obsolete_gre()
