import json

with open("bestway_product_debug_full.json", "r", encoding="utf-8") as f:
    data = json.load(f)

def find_val(obj, target, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if v == target:
                print(f"Found value '{target}' at: {path}.{k}")
            find_val(v, target, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if item == target:
                print(f"Found value '{target}' at: {path}[{i}]")
            find_val(item, target, f"{path}[{i}]")

find_val(data, "58497-7")
