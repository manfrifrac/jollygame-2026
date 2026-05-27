import sqlite3
import os
import json

def get_db_connection(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def load_data(db_path, table_name, brand):
    if not os.path.exists(db_path): return []
    conn = get_db_connection(db_path)
    prods = []
    
    # Verifichiamo se esiste la colonna is_spare_part
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = [c[1] for c in cursor.fetchall()]
    
    query = f"SELECT * FROM {table_name}"
    rows = conn.execute(query)
    
    for r in rows:
        p = dict(r)
        p['brand'] = brand
        
        # Logica Tipo
        if 'is_spare_part' in p:
            p['type'] = 'RICAMBIO' if p['is_spare_part'] == 1 else 'PRODOTTO'
        else:
            p['type'] = 'PRODOTTO'
            
        # Normalizzazione Immagini
        if brand == 'Fluidra':
            p['image'] = json.loads(p['images_json'])[0] if p.get('images_json') and p['images_json'] != '[]' else ""
            p['category'] = p.get('taxonomy', 'Senza Categoria')
        elif brand == 'Intex':
            p['image'] = p.get('image_url', p.get('images', ''))
            p['category'] = p.get('categories', 'Piscine Intex')
        elif brand == 'Bestway':
            imgs = p.get('images', '').split(',')
            p['image'] = imgs[0] if imgs else ""
            p['category'] = p.get('category', 'Bestway Generic')
            
        p['desc'] = p.get('description', p.get('description_html', ''))
        prods.append(p)
    
    conn.close()
    return prods

# Caricamento dai database puliti
f_p = load_data("fluidra_clean.db", "products", "Fluidra")
i_p = load_data("intex_clean.db", "products", "Intex")
b_p = load_data("bestway_clean.db", "bestway_products", "Bestway")

all_products = f_p + i_p + b_p
sku_map = {p['sku']: p for p in all_products if p.get('sku')}

# Relazioni (le ricarichiamo dai master o clean se presenti)
def load_rels():
    rels = {}
    if os.path.exists("fluidra_clean.db"):
        conn = sqlite3.connect("fluidra_clean.db")
        for r in conn.execute("SELECT parent_sku, child_sku FROM product_relations"):
            p, c = r[0], r[1]
            if p not in rels: rels[p] = []
            rels[p].append(c)
        conn.close()
    return rels

rels_map = load_rels()
for p in all_products:
    p['parts'] = rels_map.get(p['sku'], [])

categories = sorted(list(set(p['category'] for p in all_products if p.get('category'))))

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>JollyGame Explorer v4 - Clean Edition</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: #f4f7f6; display: flex; flex-direction: column; height: 100vh; }
        .header { background: #1a2a3a; color: white; padding: 12px 25px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.3); }
        .main { display: flex; flex: 1; overflow: hidden; }
        .sidebar { width: 380px; background: white; border-right: 1px solid #ddd; display: flex; flex-direction: column; }
        .filter-pane { padding: 15px; background: #fff; border-bottom: 1px solid #eee; }
        .product-list { flex: 1; overflow-y: auto; }
        .details { flex: 1; padding: 30px; overflow-y: auto; background: white; margin: 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        
        .item { padding: 12px 15px; border-bottom: 1px solid #f0f0f0; cursor: pointer; transition: all 0.2s; display: flex; gap: 12px; align-items: center; }
        .item:hover { background: #f0faff; border-left: 4px solid #007bff; padding-left: 11px; }
        .item img { width: 45px; height: 45px; object-fit: contain; background: #fff; border: 1px solid #eee; border-radius: 4px; }
        
        .badge { padding: 3px 7px; border-radius: 4px; font-size: 10px; font-weight: bold; color: white; text-transform: uppercase; letter-spacing: 0.5px; }
        .type-PRODOTTO { background: #28a745; }
        .type-RICAMBIO { background: #ffc107; color: #333; }
        
        .brand-fluidra { color: #004a99; font-weight: bold; font-size: 11px; }
        .brand-intex { color: #ce1126; font-weight: bold; font-size: 11px; }
        .brand-bestway { color: #008a45; font-weight: bold; font-size: 11px; }

        input, select { width: 100%; padding: 10px; margin-top: 8px; border: 1px solid #dfe3e8; border-radius: 6px; font-size: 13px; outline: none; }
        input:focus { border-color: #007bff; box-shadow: 0 0 0 2px rgba(0,123,255,0.1); }
        
        .parts-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; margin-top: 20px; }
        .part-card { border: 1px solid #eee; padding: 10px; border-radius: 8px; text-align: center; background: #f9f9f9; cursor: pointer; transition: 0.2s; }
        .part-card:hover { transform: scale(1.03); border-color: #007bff; background: #fff; }
        .part-card img { width: 70px; height: 70px; object-fit: contain; }
        
        h1 { font-size: 24px; color: #1a2a3a; margin-top: 0; }
        .ean-box { background: #f1f3f5; padding: 8px 12px; border-radius: 6px; font-family: monospace; display: inline-block; font-size: 14px; color: #495057; }
        .cat-path { font-size: 13px; color: #007bff; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <div style="font-size: 1.4em; font-weight: bold;">JollyGame Explorer v4 <span style="font-weight: 300; font-size: 0.8em;">(Clean Edition)</span></div>
        <div id="stats">Analisi dati in corso...</div>
    </div>
    
    <div class="main">
        <div class="sidebar">
            <div class="filter-pane">
                <input type="text" id="q" placeholder="Cerca SKU o Titolo..." onkeyup="filter()">
                <div style="display: flex; gap: 8px;">
                    <select id="brand" onchange="filter()">
                        <option value="">Tutti i Brand</option>
                        <option value="Fluidra">Fluidra</option>
                        <option value="Intex">Intex</option>
                        <option value="Bestway">Bestway</option>
                    </select>
                    <select id="type" onchange="filter()">
                        <option value="">Tutti i Tipi</option>
                        <option value="PRODOTTO">Prodotti Finiti</option>
                        <option value="RICAMBIO">Ricambi Tecnici</option>
                    </select>
                </div>
                <select id="category" onchange="filter()">
                    <option value="">Tutte le Categorie</option>
                    %CAT_OPTIONS%
                </select>
            </div>
            <div id="filter-status" style="padding: 8px 15px; font-size: 12px; color: #666; background: #f8f9fa;"></div>
            <div class="product-list" id="list"></div>
        </div>
        <div class="details" id="viewer">
            <div style="text-align: center; margin-top: 150px; color: #adb5bd;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                <p>Seleziona un prodotto per visualizzare la scheda tecnica pulita</p>
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
            document.getElementById('filter-status').innerText = `${current.length} elementi trovati`;
            list.innerHTML = current.slice(0, 200).map(p => `
                <div class="item" onclick="view('${p.sku}')">
                    <img src="${p.image || 'https://via.placeholder.com/45?text=?'}" onerror="this.src='https://via.placeholder.com/45?text=?'">
                    <div style="min-width:0; flex:1;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:3px;">
                            <span class="brand-${p.brand.toLowerCase()}">${p.brand}</span>
                            <span class="badge type-${p.type}">${p.type}</span>
                        </div>
                        <div style="font-size:13px; font-weight:600; color:#2c3e50; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${p.title}</div>
                        <div style="font-family:monospace; font-size:11px; color:#7f8c8d;">SKU: ${p.sku}</div>
                    </div>
                </div>
            `).join('');
        }

        function view(sku) {
            const p = skuMap[sku];
            const viewer = document.getElementById('viewer');
            
            let partsHtml = (p.parts || []).map(cs => {
                const prt = skuMap[cs] || { sku: cs, title: 'Non trovato', image: '', type: 'RICAMBIO' };
                return `<div class="part-card" onclick="view('${cs}')">
                    <img src="${prt.image || 'https://via.placeholder.com/70'}" onerror="this.src='https://via.placeholder.com/70'">
                    <div style="font-weight:bold; margin-top:5px; color:#2c3e50;">${cs}</div>
                    <div style="font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; color:#666;">${prt.title}</div>
                </div>`;
            }).join('');

            viewer.innerHTML = `
                <div class="cat-path">${p.category || 'Nessuna categoria'}</div>
                <div style="display:flex; gap:35px; margin-bottom:35px; border-bottom:1px solid #eee; padding-bottom:30px;">
                    <img src="${p.image}" style="width:280px; height:280px; object-fit:contain; background:#fff; border:1px solid #f1f3f5; border-radius:12px;" onerror="this.src='https://via.placeholder.com/280'">
                    <div style="flex:1;">
                        <span class="badge type-${p.type}">${p.type}</span>
                        <h1 style="margin:10px 0 15px 0;">${p.title}</h1>
                        <div class="ean-box">EAN: ${p.ean || 'Non Disponibile'}</div>
                        <div style="margin-top:20px; font-size:15px; color:#34495e;">
                            <strong>SKU:</strong> ${p.sku}<br>
                            <strong>Brand:</strong> ${p.brand}
                        </div>
                        <div style="margin-top:20px;">
                            <button onclick="window.open('${p.url || '#'}', '_blank')" style="background:#007bff; color:white; border:none; padding:10px 20px; border-radius:6px; cursor:pointer; font-weight:600;">Vedi Sito Originale</button>
                        </div>
                    </div>
                </div>
                
                <div style="margin-bottom:40px;">
                    <h3 style="border-left:4px solid #007bff; padding-left:12px; margin-bottom:15px;">Descrizione Tecnica</h3>
                    <div style="font-size:15px; color:#4a5568; line-height:1.7;">${p.desc || 'Nessuna descrizione disponibile per questo prodotto.'}</div>
                </div>

                ${p.parts && p.parts.length > 0 ? `
                    <div style="background:#f8fbff; padding:25px; border-radius:12px; border:1px solid #e1e9f4;">
                        <h3 style="margin-top:0;">🔧 Esploso Ricambi Correlati</h3>
                        <p style="font-size:13px; color:#666; margin-bottom:20px;">Questi componenti sono mappati nel diagramma tecnico del prodotto principale.</p>
                        <div class="parts-grid">${partsHtml}</div>
                    </div>
                ` : ''}
            `;
            viewer.scrollTop = 0;
        }

        render();
        document.getElementById('stats').innerText = `Database Totale: ${products.length} elementi`;
    </script>
</body>
</html>
"""

cat_options = "".join([f'<option value="{c}">{c}</option>' for c in categories])
final_html = html_template.replace("%PRODUCT_DATA%", json.dumps(all_products)).replace("%SKU_MAP%", json.dumps(sku_map)).replace("%CAT_OPTIONS%", cat_options)

with open("product_explorer_v4_clean.html", "w", encoding="utf-8") as f:
    f.write(final_html)

print("Browser v4 generato con successo: product_explorer_v4_clean.html")
