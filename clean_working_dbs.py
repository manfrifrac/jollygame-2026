import sqlite3
import os

def clean_database(db_path, table_name, brand):
    print(f"\n--- Pulizia {brand} ({db_path}) ---")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. ELIMINAZIONE HARD (Spazzatura)
    bad_skus = ["aggiungi al carrello", "in stock", "disponibile", "vedi dettagli", "esaurito", "null", "none", "seleziona", "n/a"]
    
    # Costruiamo la query di eliminazione per SKU spazzatura
    placeholders = ', '.join(['?'] * len(bad_skus))
    cursor.execute(f"DELETE FROM {table_name} WHERE LOWER(sku) IN ({placeholders}) OR sku IS NULL", bad_skus)
    deleted_skus = cursor.rowcount
    
    # Eliminazione per titoli vuoti o troppo corti
    cursor.execute(f"DELETE FROM {table_name} WHERE title IS NULL OR length(title) < 3 OR title IN ('.', '---', 'None', 'null')")
    deleted_titles = cursor.rowcount

    # 2. NORMALIZZAZIONE TITOLI (Sentence Case per Fluidra)
    if brand == "Fluidra":
        cursor.execute(f"SELECT sku, title FROM {table_name}")
        rows = cursor.fetchall()
        updates = []
        for sku, title in rows:
            if title and title.isupper():
                # Convertiamo in Title Case (es: "VITE INOX" -> "Vite Inox")
                new_title = title.capitalize()
                updates.append((new_title, sku))
        
        cursor.executemany(f"UPDATE {table_name} SET title = ? WHERE sku = ?", updates)
        print(f"Titoli normalizzati: {len(updates)}")

    # 3. TAGGING AUTOMATICO RICAMBI (Ferramenta)
    spare_keywords = ["vite", "dado", "rondella", "guarnizione", "o-ring", "cavo", "tappo", "raccordo", "bullone", "perno"]
    
    # Se il titolo contiene queste parole, impostiamo is_spare_part = 1
    # Nota: Aggiungiamo la colonna se non esiste (per Bestway/Intex)
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN is_spare_part INTEGER DEFAULT 0")
    except:
        pass # Esiste già

    for kw in spare_keywords:
        cursor.execute(f"UPDATE {table_name} SET is_spare_part = 1 WHERE LOWER(title) LIKE ?", (f'%{kw}%',))
    
    # Anche gli SKU che iniziano con R (Fluidra)
    if brand == "Fluidra":
        cursor.execute(f"UPDATE {table_name} SET is_spare_part = 1 WHERE sku LIKE 'R%'")

    conn.commit()
    conn.close()
    
    print(f"Record eliminati (SKU): {deleted_skus}")
    print(f"Record eliminati (Titoli): {deleted_titles}")

# Esecuzione
clean_database("fluidra_clean.db", "products", "Fluidra")
clean_database("intex_clean.db", "products", "Intex")
clean_database("bestway_clean.db", "bestway_products", "Bestway")

print("\n✅ Fase 1 completata con successo.")
