import sqlite3

def check_images():
    conn = sqlite3.connect('bestway_catalog.db')
    cursor = conn.cursor()
    
    print("=== AUDIT GALLERIA IMMAGINI BESTWAY ===")
    
    # 1. Statistiche generali sulle immagini
    cursor.execute("SELECT images FROM bestway_products")
    rows = cursor.fetchall()
    
    counts = []
    total_images = 0
    for row in rows:
        img_list = row[0].split(',') if row[0] else []
        counts.append(len(img_list))
        total_images += len(img_list)
    
    avg_images = total_images / len(counts) if counts else 0
    max_images = max(counts) if counts else 0
    min_images = min(counts) if counts else 0
    
    print(f"\nProdotti analizzati: {len(counts)}")
    print(f"Totale immagini salvate: {total_images}")
    print(f"Media immagini per prodotto: {round(avg_images, 2)}")
    print(f"Massimo immagini in un prodotto: {max_images}")
    print(f"Minimo immagini in un prodotto: {min_images}")
    
    # 2. Verifica campioni con molte immagini
    print("\nCampioni di gallerie ricche:")
    cursor.execute("SELECT sku, title, images FROM bestway_products ORDER BY length(images) DESC LIMIT 3")
    for sku, title, imgs in cursor.fetchall():
        img_list = imgs.split(',')
        print(f" - [{sku}] {title}: {len(img_list)} immagini")
        print(f"   Esempio link: {img_list[0][:100]}...")

    # 3. Verifica se ci sono prodotti con UNA SOLA immagine (potrebbero essere quelli scarsi)
    cursor.execute("SELECT COUNT(*) FROM bestway_products WHERE images NOT LIKE '%,%' AND images != ''")
    single_img = cursor.fetchone()[0]
    print(f"\nProdotti con una sola immagine: {single_img}")

    conn.close()

if __name__ == "__main__":
    check_images()
