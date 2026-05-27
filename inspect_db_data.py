import sqlite3
import json

def inspect_cleanliness():
    conn = sqlite3.connect('intex_deep_catalog.db')
    cursor = conn.cursor()
    
    print("=== CAMPIONE DI 3 PRODOTTI CASUALI ===")
    cursor.execute("SELECT title, sku, ean, price, short_description, images, pdfs, categories, attributes FROM products WHERE ean != '' AND sku != '' LIMIT 3")
    rows = cursor.fetchall()
    
    for i, row in enumerate(rows):
        title, sku, ean, price, short_desc, images, pdfs, categories, attributes = row
        print(f"\n--- Prodotto {i+1} ---")
        print(f"Titolo: {title}")
        print(f"SKU: {sku} | EAN: {ean} | Prezzo: {price}")
        
        # Clean description display (truncate if too long)
        clean_desc = short_desc.replace('\n', ' ')[:150] + '...' if short_desc else "N/A"
        print(f"Descrizione Breve: {clean_desc}")
        
        # Parse JSON fields
        try:
            img_list = json.loads(images)
            print(f"Immagini ({len(img_list)}): {img_list[0] if img_list else 'N/A'} ...")
        except: print("Immagini: Errore JSON")
        
        try:
            pdf_list = json.loads(pdfs)
            print(f"PDFs ({len(pdf_list)}): {pdf_list[0] if pdf_list else 'Nessuno'}")
        except: print("PDFs: Errore JSON")
        
        try:
            cat_list = json.loads(categories)
            print(f"Categorie: {' > '.join(cat_list)}")
        except: print("Categorie: Errore JSON")
        
        try:
            attr_dict = json.loads(attributes)
            attr_str = ", ".join([f"{k}: {v}" for k, v in list(attr_dict.items())[:3]])
            print(f"Attributi Tecnici: {attr_str} ...")
        except: print("Attributi: Errore JSON")

    # Controllo anomalie HTML o caratteri strani
    print("\n=== CONTROLLO ANOMALIE TESTUALI ===")
    cursor.execute("SELECT COUNT(*) FROM products WHERE short_description LIKE '%<%' OR title LIKE '%<%'")
    html_tags = cursor.fetchone()[0]
    print(f"Prodotti con possibili tag HTML nel titolo/descrizione: {html_tags}")
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE title LIKE '%&amp;%' OR short_description LIKE '%&amp;%'")
    html_entities = cursor.fetchone()[0]
    print(f"Prodotti con entità HTML non codificate (es. &amp;): {html_entities}")

    conn.close()

if __name__ == '__main__':
    inspect_cleanliness()
