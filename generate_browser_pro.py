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
    rels = {}
    if os.path.exists("intex_deep_catalog.db"):
        conn = get_db_connection("intex_deep_catalog.db")
        # Prodotti principali
        for r in conn.execute("SELECT * FROM products"):
            p = dict(r)
            p['brand'] = 'Intex'; p['type'] = 'PRODOTTO'
            p['image'] = p.get('image_url', '')
            p['desc'] = p.get('description', '')
            p['docs'] = []; p['parts'] = []
            all_p.append(p)
        conn.close()
    
    # Ricambi Intex (da intex_catalog.db spare_parts se disponibile)
    if os.path.exists("intex_catalog.db"):
        conn = get_db_connection("intex_catalog.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spare_parts'")
        if cursor.fetchone():
            for r in conn.execute("SELECT * FROM spare_parts"):
                p = dict(r)
                p['brand'] = 'Intex'; p['type'] = 'RICAMBIO'
                p['title'] = p.get('name', '')
                p['image'] = ''; p['desc'] = ''; p['docs'] = []
                all_p.append(p)
                # Relazione
                parent_id = p.get('product_id')
                if parent_id:
                    # Qui servirebbe mappare product_id a SKU, lo faremo approssimativo
                    pass 
        conn.close()
    return all_p, rels

def load_bestway():
    if not os.path.exists("bestway_catalog.db"): return [], {}
    conn = get_db_connection("bestway_catalog.db")
    prods = []
    for r in conn.execute("SELECT * FROM bestway_products"):
        p = dict(r)
        p['brand'] = 'Bestway'
        p['type'] = 'PRODOTTO' # Default per la tabella main
        imgs = p.get('images', '').split(',')
        p['image'] = imgs[0] if imgs else ""
        p['desc'] = p.get('description_html', '')
        p['docs'] = []
        prods.append(p)
        
    rels = {}
    child_skus = set()
    for r in conn.execute("SELECT parent_sku, child_sku FROM product_relations"):
        p, c = r['parent_sku'], r['child_sku']
        if p not in rels: rels[p] = []
        rels[p].append(c)
        child_skus.add(c)
    
    # I ricambi Bestway spesso non sono nella tabella prodotti, li aggiungiamo come schede vuote
    existing_skus = {p['sku'] for p in prods}
    for c in child_skus:
        if c not in existing_skus:
            prods.append({'sku': c, 'title': f'Ricambio {c}', 'brand': 'Bestway', 'type': 'RICAMBIO', 'image': '', 'desc': '', 'docs': []})
            
    conn.close()
    return prods, rels

# Merge
f_p, f_r = load_fluidra()
i_p, i_r = load_intex()
b_p, b_r = load_bestway()

all_products = f_p + i_p + b_p
sku_map = {p['sku']: p for p in all_products if p.get('sku')}

# Inietto le relazioni
for p in all_products:
    if p['brand'] == 'Fluidra': p['parts'] = f_r.get(p['sku'], [])
    elif p['brand'] == 'Intex': p['parts'] = i_r.get(p['sku'], [])
    elif p['brand'] == 'Bestway': p['parts'] = b_r.get(p['sku'], [])

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>JollyGame Pro Explorer v2</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: #f0f2f5; display: flex; flex-direction: column; height: 100vh; }
        .header { background: #004a99; color: white; padding: 12px 25px; display: flex; justify-content: space-between; align-items: center; }
        .main-container { display: flex; flex: 1; overflow: hidden; }
        .sidebar { width: 380px; background: white; border-right: 1px solid #ddd; display: flex; flex-direction: column; }
        .search-box { padding: 15px; border-bottom: 1px solid #eee; background: #fafafa; }
        .product-list { flex: 1; overflow-y: auto; }
        .content { flex: 1; padding: 30px; overflow-y: auto; background: white; margin: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        
        .item { padding: 10px 15px; border-bottom: 1px solid #f0f0f0; cursor: pointer; transition: background 0.1s; display: flex; gap: 12px; align-items: center; }
        .item:hover { background: #f0f7ff; }
        .item img { width: 45px; height: 45px; object-fit: contain; background: white; border: 1px solid #eee; border-radius: 4px; }
        
        .badge { padding: 2px 6px; border-radius: 4px; font-size: 0.7em; font-weight: bold; color: white; text-transform: uppercase; }
        .type-PRODOTTO { background: #007bff; }
        .type-RICAMBIO { background: #fd7e14; }
        
        .brand-fluidra { color: #004a99; font-weight: bold; font-size: 0.8em; }
        .brand-intex { color: #ce1126; font-weight: bold; font-size: 0.8em; }
        .brand-bestway { color: #008a45; font-weight: bold; font-size: 0.8em; }

        .parts-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; margin-top: 20px; }
        .part-card { border: 1px solid #eee; padding: 8px; border-radius: 6px; font-size: 0.75em; text-align: center; background: #fff; cursor: pointer; }
        .part-card:hover { border-color: #007bff; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .part-card img { width: 60px; height: 60px; object-fit: contain; }

        input, select { width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .stats-bar { font-size: 0.85em; color: #666; padding: 5px 15px; background: #eee; border-bottom: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="header">
        <div style="font-size: 1.3em; font-weight: bold;">JollyGame Explorer - Product vs Spare Parts</div>
        <div id="global-stats"></div>
    </div>
    
    <div class="main-container">
        <div class="sidebar">
            <div class="search-box">
                <input type="text" id="search" placeholder="Cerca SKU o Titolo..." onkeyup="filter()">
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <select id="brand-filter" onchange="filter()">
                        <option value="">Tutti i Brand</option>
                        <option value="Fluidra">Fluidra</option>
                        <option value="Intex">Intex</option>
                        <option value="Bestway">Bestway</option>
                    </select>
                    <select id="type-filter" onchange="filter()">
                        <option value="">Tutti i Tipi</option>
                        <option value="PRODOTTO">Solo Prodotti</option>
                        <option value="RICAMBIO">Solo Ricambi</option>
                    </select>
                </div>
            </div>
            <div class="stats-bar" id="filter-count"></div>
            <div class="product-list" id="list"></div>
        </div>
        <div class="content" id="viewer">
            <div style="text-align: center; padding-top: 100px; color: #aaa;">
                <h2>Seleziona un elemento per iniziare</h2>
                <p>Usa i filtri a sinistra per distinguere i prodotti finiti dai componenti di ricambio.</p>
            </div>
        </div>
    </div>

    <script>
        const products = %PRODUCT_DATA%;
        const skuMap = %SKU_MAP%;
        let filtered = products;

        function filter() {
            const q = document.getElementById('search').value.toLowerCase();
            const b = document.getElementById('brand-filter').value;
            const t = document.getElementById('type-filter').value;
            
            filtered = products.filter(p => {
                const matchQ = (p.sku || '').toLowerCase().includes(q) || (p.title || '').toLowerCase().includes(q);
                const matchB = b === "" || p.brand === b;
                const matchT = t === "" || p.type === t;
                return matchQ && matchB && matchT;
            });
            renderList();
        }

        function renderList() {
            const list = document.getElementById('list');
            document.getElementById('filter-count').innerText = `Risultati: ${filtered.length}`;
            list.innerHTML = filtered.slice(0, 300).map(p => `
                <div class="item" onclick="view('${p.sku}')">
                    <img src="${p.image || 'https://via.placeholder.com/45?text=?'}" onerror="this.src='https://via.placeholder.com/45?text=ERR'">
                    <div style="flex:1; min-width:0;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span class="brand-${p.brand.toLowerCase()}">${p.brand}</span>
                            <span class="badge type-${p.type}">${p.type}</span>
                        </div>
                        <div style="font-weight:600; font-size:0.85em; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${p.title}</div>
                        <div style="font-family:monospace; font-size:0.75em; color:#777;">${p.sku}</div>
                    </div>
                </div>
            `).join('');
        }

        function view(sku) {
            const p = skuMap[sku];
            if(!p) return;
            const viewer = document.getElementById('viewer');
            
            let partsHtml = (p.parts || []).map(childSku => {
                const part = skuMap[childSku] || { sku: childSku, title: 'Dati non caricati', image: '', type: 'RICAMBIO' };
                return `
                    <div class="part-card" onclick="view('${childSku}')">
                        <img src="${part.image || 'https://via.placeholder.com/60?text=?'}" onerror="this.src='https://via.placeholder.com/60?text=?'}">
                        <div style="font-weight: bold; margin-top:4px;">${part.sku}</div>
                        <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color:#666;">${part.title}</div>
                    </div>
                `;
            }).join('');

            viewer.innerHTML = `
                <div style="display:flex; gap:30px; border-bottom:1px solid #eee; padding-bottom:20px; margin-bottom:20px;">
                    <img src="${p.image}" style="width:250px; height:250px; object-fit:contain; border:1px solid #eee; border-radius:8px;" onerror="this.src='https://via.placeholder.com/250?text=No+Image'">
                    <div style="flex:1">
                        <span class="badge type-${p.type}">${p.type}</span>
                        <span class="brand-${p.brand.toLowerCase()}" style="margin-left:10px; font-size:1.1em;">${p.brand}</span>
                        <h1 style="margin: 10px 0;">${p.title}</h1>
                        <p style="font-family:monospace; background:#f8f9fa; padding:5px 10px; border-radius:4px; display:inline-block;">SKU: ${p.sku} | EAN: ${p.ean || 'N/A'}</p>
                        
                        <div style="margin-top:20px;">
                            <strong>Documentazione:</strong><br>
                            ${(p.docs || []).length > 0 ? p.docs.map(d => `<a href="${d.url}" target="_blank" style="margin-right:10px; text-decoration:none; color:#004a99;">📄 ${d.title}</a>`).join('') : 'Nessun PDF'}
                        </div>
                    </div>
                </div>

                <div style="margin-bottom:30px;">
                    <h3>Dettagli Tecnici</h3>
                    <div style="font-size:0.95em; color:#333; line-height:1.5;">${p.desc || 'Descrizione non disponibile.'}</div>
                </div>

                ${p.type === 'PRODOTTO' ? `
                    <div style="background:#f8f9fa; padding:20px; border-radius:8px; border:1px solid #e9ecef;">
                        <h3>📦 Esploso Ricambi (Click per dettagli)</h3>
                        <div class="parts-grid">${partsHtml || 'Nessun ricambio collegato.'}</div>
                    </div>
                ` : ''}
            `;
            viewer.scrollTop = 0;
        }

        // Stats iniziali
        const prodCount = products.filter(p => p.type === 'PRODOTTO').length;
        const spareCount = products.filter(p => p.type === 'RICAMBIO').length;
        document.getElementById('global-stats').innerText = `Prodotti: ${prodCount} | Ricambi: ${spareCount}`;

        renderList();
    </script>
</body>
</html>
"""

final_html = html_template.replace("%PRODUCT_DATA%", json.dumps(all_products)).replace("%SKU_MAP%", json.dumps(sku_map))
with open("product_explorer_pro_v2.html", "w", encoding="utf-8") as f:
    f.write(final_html)

print("Browser Pro v2 generato con successo: product_explorer_pro_v2.html")
