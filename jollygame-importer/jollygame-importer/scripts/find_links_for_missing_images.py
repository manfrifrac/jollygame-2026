import json
import os

def find_images_in_crawled_links():
    dump_path = "master_catalog_dump.json"
    links_path = "gre_all_product_links.json"
    
    if not os.path.exists(dump_path) or not os.path.exists(links_path):
        print(f"File non trovati: {dump_path}={os.path.exists(dump_path)}, {links_path}={os.path.exists(links_path)}")
        return

    with open(dump_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    with open(links_path, 'r', encoding='utf-8') as f:
        links = json.load(f)

    missing = [p for p in catalog if p['mediaCount']['count'] == 0 and p['variants']['nodes'][0].get('sku')]
    print(f"🔍 Analisi di {len(missing)} prodotti senza foto...")

    matches = []
    for p in missing:
        sku = p['variants']['nodes'][0].get('sku', '').lower()
        title = p['title'].lower()
        
        # Try to find a link that contains the SKU or part of the title
        found_link = None
        for link in links:
            if sku and sku in link.lower():
                found_link = link
                break
        
        if not found_link:
            # Try to match slugified title
            slug = title.replace(' ', '-').replace('"', '').replace(' kit ', '')
            for link in links:
                if slug in link.lower() or link.lower().endswith(slug):
                    found_link = link
                    break
        
        if found_link:
            matches.append({
                "id": p['id'],
                "sku": sku,
                "title": p['title'],
                "url": found_link
            })

    print(f"✅ Trovati {len(matches)} possibili URL per prodotti senza foto.")
    
    with open("jollygame-importer/jollygame-importer/products_to_scrape_images.json", "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2)

if __name__ == "__main__":
    find_images_in_crawled_links()
