import csv
import json
import os
import requests
from collections import Counter

def quality_audit(file_path):
    if not os.path.exists(file_path):
        return "File not found"

    report = {
        "completeness": {
            "missing_sku": 0,
            "missing_ean": 0,
            "missing_price": 0,
            "missing_images": 0,
            "total_variants": 0
        },
        "taxonomy": {
            "categories": Counter(),
            "brands": Counter()
        },
        "master_stats": {
            "total_masters": 0,
            "avg_variants_per_master": 0
        },
        "samples": []
    }

    master_variant_map = {}

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            report["completeness"]["total_variants"] += 1
            
            # 1. Completeness
            if not row.get('SKU'): report["completeness"]["missing_sku"] += 1
            ean = row.get('EAN', '').strip()
            if not ean or ean.lower() == 'none' or len(ean) < 8:
                report["completeness"]["missing_ean"] += 1
            
            try:
                if float(row.get('Prezzo', 0)) <= 0:
                    report["completeness"]["missing_price"] += 1
            except:
                report["completeness"]["missing_price"] += 1
                
            imgs = row.get('Immagini_JSON', '[]')
            if imgs == '[]' or len(imgs) < 10:
                report["completeness"]["missing_images"] += 1

            # 2. Grouping
            master = row['Master_Title']
            if master not in master_variant_map:
                master_variant_map[master] = []
            master_variant_map[master].append(row)
            
            # 3. Taxonomy
            tags = row['Tags'].split(',')
            for t in tags:
                if t.startswith('Categoria:'):
                    report["taxonomy"]["categories"][t] += 1
                if t.startswith('Brand:'):
                    report["taxonomy"]["brands"][t] += 1

    report["master_stats"]["total_masters"] = len(master_variant_map)
    report["master_stats"]["avg_variants_per_master"] = round(report["completeness"]["total_variants"] / len(master_variant_map), 1)

    # Pick some samples for visual check in report
    for i, (m, variants) in enumerate(list(master_variant_map.items())[:5]):
        report["samples"].append({
            "master": m,
            "variants_count": len(variants),
            "first_variant_sku": variants[0]['SKU'],
            "first_variant_detail": row.get('Variant_Detail', 'Standard')
        })

    return report

res = quality_audit('gold_consolidated_final.csv')
print(json.dumps(res, indent=2))
