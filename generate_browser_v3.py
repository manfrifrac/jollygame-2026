import sqlite3
import os
import json

def get_db_connection(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def load_fluidra():
    if not os.path.exists("fluidra_catalog.db"): return [], {}
    conn = get_db_connection("fluidra_catalog.db")
    prods = []
    for r in conn.execute("SELECT * FROM products"):
        p = dict(r)
        p['brand'] = 'Fluidra'
        p['type'] = 'RICAMBIO' if p.get('is_spare_part') == 1 else 'PRODOTTO'
        p['image'] = json.loads(p['images_json'])[0] if p.get('images_json') and p['images_json'] != '[]' else ""
        p['desc'] = p.get('description', '')
        p['category'] = p.get('taxonomy', 'Senza Categoria')
        p['docs'] = json.loads(p.get('docs_json', '[]'))
        prods.append(p)
    
    rels = {}
    for r in conn.execute("SELECT parent_sku, child_sku FROM product_relations"):
        p, c = r['parent_sku'], r['child_sku']
        if p not in rels: rels[p] = []
        rels[p].append(c)
    conn.close()
    return prods, rels

def load_intex():
    all_p = []
    if os.path.exists("intex_deep_catalog.db"):
        conn = get_db_connection("intex_deep_catalog.db")
        for r in conn.execute("SELECT * FROM products"):
            p = dict(r)
            p['brand'] = 'Intex'; p['type'] = 'PRODOTTO'
            p['image'] = p.get('image_url', p.get('images', ''))
            p['desc'] = p.get('description', '')
            p['category'] = p.get('categories', 'Piscine Intex')
            p['docs'] = []; p['parts'] = []
            all_p.append(p)
        conn.close()
    return all_p, {}

def load_bestway():
    if not os.path.exists("bestway_catalog.db"): return [], {}
    conn = get_db_connection("bestway_catalog.db")
    prods = []
    for r in conn.execute("SELECT * FROM bestway_products"):
        p = dict(r)
        p['brand'] = 'Bestway'; p['type'] = 'PRODOTTO'
        imgs = p.get('images', '').split(',')
        p['image'] = imgs[0] if imgs else ""
        p['desc'] = p.get('description_html', '')
        p['category'] = p.get('category', 'Bestway Generic')
        p['docs'] = []
        prods.append(p)
    conn.close()
    return prods, {}

# Merge dati
f_p, f_r = load_fluidra()
i_p, i_r = load_intex()
b_p, b_r = load_bestway()
all_products = f_p + i_p + b_p
sku_map = {p['sku']: p for p in all_products if p.get('sku')}

# Inietto relazioni
for p in all_products:
    if p['brand'] == 'Fluidra': p['parts'] = f_r.get(p['sku'], [])
    else: p['parts'] = []

# Estraggo categorie uniche per il filtro
categories = sorted(list(set(p['category'] for p in all_products if p.get('category'))))

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>JollyGame Explorer v3 - Categorie</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #f0f2f5; display: flex; flex-direction: column; height: 100vh; }
        .header { background: #003366; color: white; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; }
        .main { display: flex; flex: 1; overflow: hidden; }
        .sidebar { width: 400px; background: white; border-right: 1px solid #ddd; display: flex; flex-direction: column; }
        .search-area { padding: 15px; background: #f8f9fa; border-bottom: 1px solid #ddd; }
        .product-list { flex: 1; overflow-y: auto; }
        .details { flex: 1; padding: 30px; overflow-y: auto; background: white; margin: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        
        .item { padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; display: flex; gap: 10px; }
        .item:hover { background: #eef6ff; }
        .item img { width: 50px; height: 50px; object-fit: contain; background: white; border: 1px solid #ddd; }
        
        .badge { padding: 2px 5px; border-radius: 3px; font-size: 10px; font-weight: bold; color: white; text-transform: uppercase; }
        .type-PRODOTTO { background: #007bff; }
        .type-RICAMBIO { background: #fd7e14; }
        
        .cat-tag { font-size: 11px; color: #0056b3; background: #e7f3ff; padding: 2px 5px; border-radius: 3px; display: inline-block; margin-top: 5px; }
        
        input, select { width: 100%; padding: 8px; margin-bottom: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; }
        .parts-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 10px; }
        .part-item { border: 1px solid #eee; padding: 5px; text-align: center; font-size: 11px; cursor: pointer; }
        .part-item:hover { border-color: #007bff; }
    </style>
</head>
<body>
    <div class="header">
        <div style="font-weight: bold; font-size: 1.2em;">JollyGame Explorer v3 - Catalogo & Categorie</div>
        <div id="stats"></div>
    </div>
    <div class="main">
        <div class="sidebar">
            <div class="search-area">
                <input type="text" id="q" placeholder="Cerca per SKU o Titolo..." onkeyup="filter()">
                <div style="display: flex; gap: 5px;">
                    <select id="brand" onchange="filter()">
                        <option value="">Tutti i Brand</option>
                        <option value="Fluidra">Fluidra</option>
                        <option value="Intex">Intex</option>
                        <option value="Bestway">Bestway</option>
                    </select>
                    <select id="type" onchange="filter()">
                        <option value="">Tutti i Tipi</option>
                        <option value="PRODOTTO">Prodotti</option>
                        <option value="RICAMBIO">Ricambi</option>
                    </select>
                </div>
                <select id="category" onchange="filter()">
                    <option value="">Tutte le Categorie</option>
                    %CAT_OPTIONS%
                </select>
            </div>
            <div class="product-list" id="list"></div>
        </div>
        <div class="details" id="viewer">
            <div style="text-align: center; margin-top: 100px; color: #999;">
                <h2>Seleziona un prodotto per vedere i dettagli e la categoria</h2>
            </div>
        </div>
    </div>

    <script>
        const products = %PRODUCT_DATA%;
        const skuMap = %SKU_MAP%;
        let current = products;

        function filter() {
            const q = document.getElementById('q').value.toLowerCase();
            const b = document.getElementById('brand').value;
            const t = document.getElementById('type').value;
            const c = document.getElementById('category').value;
            
            current = products.filter(p => {
                const matchQ = (p.sku || '').toLowerCase().includes(q) || (p.title || '').toLowerCase().includes(q);
                const matchB = b === "" || p.brand === b;
                const matchT = t === "" || p.type === t;
                const matchC = c === "" || p.category === c;
                return matchQ && matchB && matchT && matchC;
            });
            render();
        }

        function render() {
            const list = document.getElementById('list');
            document.getElementById('stats').innerText = `Visualizzati: ${current.length}`;
            list.innerHTML = current.slice(0, 300).map(p => `
                <div class="item" onclick="view('${p.sku}')">
                    <img src="${p.image || 'https://via.placeholder.com/50'}" onerror="this.src='https://via.placeholder.com/50'">
                    <div style="min-width:0; flex:1;">
                        <div style="display:flex; justify-content:space-between;">
                            <span style="font-weight:bold; font-size:11px;">${p.brand}</span>
                            <span class="badge type-${p.type}">${p.type}</span>
                        </div>
                        <div style="font-size:13px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${p.title}</div>
                        <div style="font-size:11px; color:#666;">SKU: ${p.sku}</div>
                        <div class="cat-tag">${p.category}</div>
                    </div>
                </div>
            `).join('');
        }

        function view(sku) {
            const p = skuMap[sku];
            const viewer = document.getElementById('viewer');
            
            let partsHtml = (p.parts || []).map(cs => {
                const prt = skuMap[cs] || { sku: cs, title: 'Non trovato', image: '' };
                return `<div class="part-item" onclick="view('${cs}')">
                    <img src="${prt.image || 'https://via.placeholder.com/60'}" style="width:60px; height:60px; object-fit:contain;"><br>
                    <b>${cs}</b><br>${prt.title}
                </div>`;
            }).join('');

            viewer.innerHTML = `
                <div style="display:flex; gap:20px; border-bottom:1px solid #eee; padding-bottom:20px;">
                    <img src="${p.image}" style="width:250px; height:250px; object-fit:contain; border:1px solid #ddd;" onerror="this.src='https://via.placeholder.com/250'">
                    <div style="flex:1;">
                        <span class="badge type-${p.type}">${p.type}</span>
                        <h1 style="margin:5px 0;">${p.title}</h1>
                        <p style="background:#f8f9fa; padding:5px; border-radius:3px; display:inline-block; font-family:monospace;">SKU: ${p.sku} | EAN: ${p.ean || 'N/A'}</p>
                        <div style="margin-top:10px;">
                            <b>Categoria:</b><br>
                            <span class="cat-tag" style="font-size:14px;">${p.category}</span>
                        </div>
                    </div>
                </div>
                <div style="margin-top:20px;">
                    <h3>Descrizione Tecnica</h3>
                    <div style="color:#444; line-height:1.5;">${p.desc || 'Nessuna descrizione.'}</div>
                </div>
                ${p.parts && p.parts.length > 0 ? `
                    <div style="margin-top:30px; background:#f0f7ff; padding:15px; border-radius:8px;">
                        <h3>Esploso Ricambi Correlati</h3>
                        <div class="parts-grid">${partsHtml}</div>
                    </div>
                ` : ''}
            `;
            viewer.scrollTop = 0;
        }

        render();
    </script>
</body>
</html>
"""

cat_options = "".join([f'<option value="{c}">{c}</option>' for c in categories])
final_html = html_template.replace("%PRODUCT_DATA%", json.dumps(all_products)).replace("%SKU_MAP%", json.dumps(sku_map)).replace("%CAT_OPTIONS%", cat_options)

with open("product_explorer_v3.html", "w", encoding="utf-8") as f:
    f.write(final_html)

print("Browser v3 generato con successo: product_explorer_v3.html")
