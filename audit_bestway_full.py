import sqlite3
import json

def full_audit():
    conn = sqlite3.connect('bestway_catalog.db')
    cursor = conn.cursor()

    print("="*50)
    print("   AUDIT COMPLETO DATABASE BESTWAY (POST-ENRICH)   ")
    print("="*50)

    # 1. Statistiche Generali
    cursor.execute("SELECT COUNT(*) FROM bestway_products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bestway_products WHERE category LIKE 'Ricambi%'")
    total_spare_parts = cursor.fetchone()[0]
    
    total_originals = total_products - total_spare_parts

    print(f"\n📊 PANORAMICA NUMERICA:")
    print(f" - Totale Prodotti nel DB: {total_products}")
    print(f" - Prodotti Principali (Scraping Iniziale): {total_originals}")
    print(f" - Pezzi di Ricambio (Estratti dagli Esplosi): {total_spare_parts}")

    # 2. Qualità dei Dati - Prodotti Principali
    print(f"\n✅ QUALITÀ DATI - PRODOTTI PRINCIPALI ({total_originals}):")
    cursor.execute("SELECT COUNT(*) FROM bestway_products WHERE category NOT LIKE 'Ricambi%' AND (ean IS NOT NULL AND ean != '')")
    with_ean = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bestway_products WHERE category NOT LIKE 'Ricambi%' AND (images IS NOT NULL AND images != '')")
    with_images = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bestway_products WHERE category NOT LIKE 'Ricambi%' AND (specs_json IS NOT NULL AND specs_json != '{}')")
    with_specs = cursor.fetchone()[0]

    print(f" - Con EAN valido: {with_ean} ({round(with_ean/total_originals*100, 1)}%)")
    print(f" - Con Immagini: {with_images} ({round(with_images/total_originals*100, 1)}%)")
    print(f" - Con Specifiche Tecniche JSON: {with_specs} ({round(with_specs/total_originals*100, 1)}%)")

    # 3. Qualità dei Dati - Ricambi
    print(f"\n⚙️ QUALITÀ DATI - PEZZI DI RICAMBIO ({total_spare_parts}):")
    cursor.execute("SELECT COUNT(*) FROM bestway_products WHERE category LIKE 'Ricambi%' AND price IS NOT NULL AND price > 0")
    with_price_sp = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bestway_products WHERE category LIKE 'Ricambi%' AND (images IS NOT NULL AND images != '')")
    with_images_sp = cursor.fetchone()[0]

    print(f" - Con Prezzo: {with_price_sp} ({round(with_price_sp/total_spare_parts*100, 1) if total_spare_parts > 0 else 0}%)")
    print(f" - Con Immagine: {with_images_sp} ({round(with_images_sp/total_spare_parts*100, 1) if total_spare_parts > 0 else 0}%)")

    # 4. Relazioni Mappate
    cursor.execute("SELECT COUNT(*) FROM product_relations")
    total_relations = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT parent_sku) FROM product_relations WHERE relation_type = 'spare_part'")
    products_with_sp = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT parent_sku) FROM product_relations WHERE relation_type = 'related'")
    products_with_rel = cursor.fetchone()[0]

    print(f"\n🔗 RELAZIONI E COMPATIBILITÀ:")
    print(f" - Totale Relazioni Mappate: {total_relations}")
    print(f" - Prodotti Principali che hanno Ricambi collegati: {products_with_sp}")
    print(f" - Prodotti Principali con Accessori/Correlati: {products_with_rel}")

    # Top 5 prodotti con più ricambi
    print(f"\n🏆 TOP 5 PRODOTTI CON PIÙ RICAMBI (Esplosi più complessi):")
    cursor.execute('''
        SELECT p.sku, p.title, COUNT(r.child_sku) as sp_count
        FROM product_relations r
        JOIN bestway_products p ON r.parent_sku = p.sku
        WHERE r.relation_type = 'spare_part'
        GROUP BY p.sku
        ORDER BY sp_count DESC
        LIMIT 5
    ''')
    for sku, title, count in cursor.fetchall():
        print(f" - [{sku}] {title[:60]}... -> {count} pezzi")

    # 5. Analisi Categorie Principali (Escludendo i ricambi)
    print(f"\n📂 MACRO-CATEGORIE PRINCIPALI:")
    cursor.execute('''
        SELECT 
            SUBSTR(category, 1, INSTR(category || ' >', ' >') - 1) as macro, 
            COUNT(*) 
        FROM bestway_products 
        WHERE category NOT LIKE 'Ricambi%'
        GROUP BY macro
        ORDER BY COUNT(*) DESC
        LIMIT 5
    ''')
    for macro, count in cursor.fetchall():
        if macro:
            print(f" - {macro}: {count} prodotti")

    print("\n" + "="*50)
    conn.close()

if __name__ == "__main__":
    full_audit()
