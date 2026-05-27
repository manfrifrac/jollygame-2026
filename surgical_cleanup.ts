import csv
from collections import Counter, defaultdict

def surgical_audit(files):
    for f in files:
        brand = f.split('_')[1].capitalize()
        groups = defaultdict(list)
        
        with open(f, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                title = row['Titolo'].lower()
                price = float(row['Prezzo'])
                
                # Definizione gruppi chirurgici
                if 'cartucc' in title: grp = "Cartucce Filtro (Consumabili)"
                elif 'telo' in title or 'copertura' in title: grp = "Teli e Coperture"
                elif 'pompa' in title or 'filtro' in title or 'sand' in title: grp = "Pompe e Sistemi Filtrazione"
                elif 'piscina' in title or 'spa' in title or 'idromassaggio' in title: grp = "Vasche (Piscine/SPA)"
                elif 'tubo' in title or 'raccordo' in title or 'adattatore' in title or 'valvola' in title: grp = "Idraulica (Tubi/Valvole)"
                elif 'scaletta' in title: grp = "Scalette"
                elif 'luce' in title or 'led' in title or 'faro' in title: grp = "Illuminazione"
                elif 'pulitore' in title or 'robot' in title or 'aspiratore' in title or 'spazzola' in title or 'retino' in title: grp = "Pulizia e Manutenzione"
                elif 'tappeto' in title or 'base' in title or 'piastrella' in title: grp = "Protezione Fondo/Tappeti"
                else: grp = "Altro/Minuteria Tecnica"
                
                groups[grp].append(price)
        
        print(f"\n--- {brand.upper()} DETTAGLIO CHIRURGICO ---")
        for grp, prices in sorted(groups.items(), key=lambda x: len(x[1]), reverse=True):
            avg_price = sum(prices)/len(prices)
            print(f"  - {grp}: {len(prices)} prodotti (Media: €{avg_price:.2f})")

surgical_audit(["gold_intex_final.csv", "gold_bestway_final.csv", "gold_fluidra_final.csv"])
