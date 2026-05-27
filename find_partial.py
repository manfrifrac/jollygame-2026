import json

with open("bestway_product_debug_full.json", "r", encoding="utf-8") as f:
    data = json.load(f)

def find_partial_val(obj, target, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and target in v:
                print(f"Found partial match '{target}' at: {path}.{k} -> {v[:50]}...")
            find_partial_val(v, target, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str) and target in item:
                print(f"Found partial match '{target}' at: {path}[{i}] -> {item[:50]}...")
            find_partial_val(item, target, f"{path}[{i}]")

find_partial_val(data, "Pompa di filtraggio a sabbia")
