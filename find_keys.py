import json

with open("bestway_product_debug_full.json", "r", encoding="utf-8") as f:
    data = json.load(f)

def find_key(obj, target, path=""):
    if isinstance(obj, dict):
        if target in obj:
            print(f"Found '{target}' at: {path}.{target}")
        for k, v in obj.items():
            find_key(v, target, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            find_key(item, target, f"{path}[{i}]")

find_key(data, "product")
find_key(data, "relatedProducts")
find_key(data, "spareParts")
