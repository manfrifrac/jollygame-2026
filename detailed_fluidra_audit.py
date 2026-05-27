import sqlite3
import json
import os
import re

def rigorous_fluidra_audit():
    db_path = "fluidra_clean.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Prendiamo i 5204 prodotti che abbiamo precedentemente isolato come "commerciali"
    # Useremo la stessa logica di base ma con un'analisi più granulare
    cursor.execute("SELECT sku, title, taxonomy, images_json FROM products WHERE is_spare_part = 0")
    rows = cursor.fetchall()
    
    # Classificazione
    categories = {
        "MACCHINE_E_SISTEMI": [], # Robot, Pompe, Elettrolisi, Filtri, Pompe Calore
        "ACCESSORI_ESTERNI": [],  # Scale, Docce, Trampolini, Griglie
        "COMPONENTI_IDRAULICI": [], # Valvole, Skimmer, Bocchette, Scarichi, Raccordi complessi
        "COMPONENTI_ELETTRICI": [], # Fari, Scatole derivazione, Trasformatori
        "TECNICO_SOSPETTO": [],     # Cose che sembrano ricambi ma sono sfuggite (es. Flange, Riduzioni)
        "DA_SCARTARE": []           # Errori, titoli numerici, etc.
    }

    # Keyword per Macchine (Prodotti di punta)
    kw_macchine = ["robot", "pulitore", "pompa", "filtro", "cloratore", "elettrolisi", "e-next", "vortex", "cnx", "calore", "scambiatore"]
    # Keyword per Esterni
    kw_esterni = ["scala", "gradino", "doccia", "griglia", "copertura", "telo", "avvolgitore", "trampolino", "corrimano"]
    # Keyword per Idraulica (Prodotti necessari ma meno "commerciali")
    kw_idraulica = ["valvola", "skimmer", "scarico", "bocchetta", "presa", "giunto", "collettore", "misuratore", "livello"]
    # Keyword per Elettrica
    kw_elettrica = ["faro", "lampada", "led", "trasformatore", "quadro", "scatola", "sensore", "sonda", "elettrodo"]
    # Keyword per Tecnico/Ricambio (Da declassare probabilmente)
    kw_tecnico = ["flangia", "riduzione", "nipplo", "raccordo", "tubo", "staffa", "piastra", "adattatore", "connettore", "ghiera"]

    for r in rows:
        title = str(r['title']).lower()
        tax = str(r['taxonomy']).lower()
        sku = str(r['sku']).upper()
        
        # Filtro spazzatura numerica
        if re.match(r'^\d+$', title.replace(" ", "")) or len(title) < 5 or sku == "AGGIUNGI AL CARRELLO":
            categories["DA_SCARTARE"].append(dict(r))
            continue

        # Classificazione per importanza commerciale
        if any(k in title or k in tax for k in kw_macchine):
            categories["MACCHINE_E_SISTEMI"].append(dict(r))
        elif any(k in title or k in tax for k in kw_esterni):
            categories["ACCESSORI_ESTERNI"].append(dict(r))
        elif any(k in title or k in tax for k in kw_elettrica):
            categories["COMPONENTI_ELETTRICI"].append(dict(r))
        elif any(k in title or k in tax for k in kw_idraulica):
            categories["COMPONENTI_IDRAULICI"].append(dict(r))
        elif any(k in title or k in tax for k in kw_tecnico):
            categories["TECNICO_SOSPETTO"].append(dict(r))
        else:
            categories["TECNICO_SOSPETTO"].append(dict(r))

    conn.close()
    
    summary = {k: len(v) for k, v in categories.items()}
    samples = {k: [f"{x['sku']} | {x['title']}" for x in v[:10]] for k, v in categories.items()}
    
    return {
        "riepilogo": summary,
        "esempi": samples
    }

print(json.dumps(rigorous_fluidra_audit(), indent=2))
