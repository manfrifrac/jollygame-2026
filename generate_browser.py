import sqlite3
import os
import json

def get_data(db_path, table_name, mapping):
    if not os.path.exists(db_path): return []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = [c[1] for c in cursor.fetchall()]
    
    # Filter mapping to existing columns
    active_mapping = {k: v for k, v in mapping.items() if v in cols}
    cols_str = ", ".join(active_mapping.values())
    
    cursor.execute(f"SELECT {cols_str} FROM {table_name}")
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        item = dict(zip(active_mapping.keys(), row))
        # Handle Fluidra image list
        if 'image' in item and item['image'] and item['image'].startswith('['):
            try:
                imgs = json.loads(item['image'])
                item['image'] = imgs[0] if imgs else ""
            except: pass
        results.append(item)
    
    conn.close()
    return results

# Mappings specifici
fluidra_data = get_data("fluidra_catalog.db", "products", {"sku": "sku", "title": "title", "ean": "ean", "image": "images_json"})
intex_data = get_data("intex_deep_catalog.db", "products", {"sku": "sku", "title": "title", "ean": "ean", "image": "image_url"})
bestway_data = get_data("bestway_catalog.db", "bestway_products", {"sku": "sku", "title": "title", "ean": "ean", "image": "image_url"})

all_products = []
for p in fluidra_data: p['brand'] = 'Fluidra'; all_products.append(p)
for p in intex_data: p['brand'] = 'Intex'; all_products.append(p)
for p in bestway_data: p['brand'] = 'Bestway'; all_products.append(p)

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>JollyGame Product Browser</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background: #f4f4f9; }
        .controls { position: sticky; top: 0; background: white; padding: 15px; border-bottom: 2px solid #ddd; z-index: 100; display: flex; gap: 10px; align-items: center; }
        input, select { padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin-top: 20px; }
        .card { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 15px; display: flex; flex-direction: column; transition: transform 0.2s; }
        .card:hover { transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .card img { width: 100%; height: 200px; object-fit: contain; background: #eee; border-radius: 4px; }
        .brand { font-size: 0.8em; color: #666; text-transform: uppercase; margin-top: 10px; }
        .title { font-weight: bold; margin: 5px 0; height: 3em; overflow: hidden; }
        .sku { font-family: monospace; color: #444; }
        .ean { font-size: 0.9em; margin-top: 5px; }
        .ean.missing { color: #d9534f; font-weight: bold; }
        .ean.ok { color: #5cb85c; }
        .stats { margin-bottom: 10px; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Catalogo Prodotti JollyGame (Anteprima Revisione)</h1>
    <div class="stats">Totale prodotti caricati: <span id="total-count">0</span></div>
    
    <div class="controls">
        <input type="text" id="search" placeholder="Cerca per SKU o Titolo..." onkeyup="filter()">
        <select id="brand-filter" onchange="filter()">
            <option value="">Tutti i Brand</option>
            <option value="Fluidra">Fluidra</option>
            <option value="Intex">Intex</option>
            <option value="Bestway">Bestway</option>
        </select>
        <select id="ean-filter" onchange="filter()">
            <option value="">Tutti gli stati EAN</option>
            <option value="ok">Con EAN</option>
            <option value="missing">Senza EAN</option>
        </select>
    </div>

    <div class="grid" id="product-grid"></div>

    <script>
        const products = %PRODUCT_DATA%;
        
        function filter() {
            const searchTerm = document.getElementById('search').value.toLowerCase();
            const brandTerm = document.getElementById('brand-filter').value;
            const eanTerm = document.getElementById('ean-filter').value;
            
            const filtered = products.filter(p => {
                const matchesSearch = (p.sku || '').toLowerCase().includes(searchTerm) || (p.title || '').toLowerCase().includes(searchTerm);
                const matchesBrand = brandTerm === "" || p.brand === brandTerm;
                const hasEan = p.ean && p.ean.trim() !== "";
                const matchesEan = eanTerm === "" || (eanTerm === "ok" ? hasEan : !hasEan);
                return matchesSearch && matchesBrand && matchesEan;
            });
            
            render(filtered);
        }

        function render(data) {
            const grid = document.getElementById('product-grid');
            document.getElementById('total-count').innerText = data.length;
            grid.innerHTML = data.slice(0, 1000).map(p => `
                <div class="card">
                    <img src="${p.image || 'https://via.placeholder.com/200?text=No+Image'}" onerror="this.src='https://via.placeholder.com/200?text=Error'">
                    <div class="brand">${p.brand}</div>
                    <div class="title">${p.title || 'Senza Titolo'}</div>
                    <div class="sku">SKU: ${p.sku || 'N/A'}</div>
                    <div class="ean ${p.ean ? 'ok' : 'missing'}">
                        EAN: ${p.ean || 'MANCANTE'}
                    </div>
                </div>
            `).join('');
            
            if (data.length > 1000) {
                grid.innerHTML += '<div style="grid-column: 1/-1; text-align: center; padding: 20px;">Visualizzati solo i primi 1000 prodotti. Usa i filtri per restringere la ricerca.</div>';
            }
        }

        render(products);
    </script>
</body>
</html>
"""

final_html = html_template.replace("%PRODUCT_DATA%", json.dumps(all_products))

with open("product_browser.html", "w", encoding="utf-8") as f:
    f.write(final_html)

print("Browser generato con successo: product_browser.html")
print(f"Totale prodotti inclusi: {len(all_products)}")
