import json
import csv
import os

def convert_to_csv():
    if not os.path.exists("intex_full_catalog.json"):
        print("Error: intex_full_catalog.json not found.")
        return

    with open("intex_full_catalog.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Products CSV
    product_headers = ["source", "url", "title", "sku", "short_description", "images"]
    with open("intex_products.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=product_headers, extrasaction='ignore')
        writer.writeheader()
        for item in data:
            # Flatten images list
            row = item.copy()
            row["images"] = " | ".join(item.get("images", []))
            writer.writerow(row)

    # 2. Spare Parts CSV (linked by Parent URL)
    spare_headers = ["parent_url", "parent_title", "ref", "sku", "name", "price", "stock", "url"]
    with open("intex_spare_parts.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=spare_headers)
        writer.writeheader()
        for item in data:
            for spare in item.get("spare_parts", []):
                spare_row = {
                    "parent_url": item["url"],
                    "parent_title": item["title"],
                    "ref": spare.get("ref", ""),
                    "sku": spare.get("sku", ""),
                    "name": spare.get("name", ""),
                    "price": spare.get("price", ""),
                    "stock": spare.get("stock", ""),
                    "url": spare.get("url", "")
                }
                writer.writerow(spare_row)

    print("Conversion complete: intex_products.csv and intex_spare_parts.csv created.")

if __name__ == "__main__":
    convert_to_csv()
