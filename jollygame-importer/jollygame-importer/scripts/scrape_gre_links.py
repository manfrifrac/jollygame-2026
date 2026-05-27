import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os
import random

async def scrape_gre_links():
    with open("gre_categories.json", "r", encoding="utf-8") as f:
        categories = json.load(f)

    all_links = set()
    output_file = "gre_all_product_links.json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)

        for cat in categories:
            print(f"📂 Scansione categoria: {cat['label']}")
            current_url = cat['url']
            
            while current_url:
                try:
                    await page.goto(current_url, wait_until="load", timeout=60000)
                    await page.wait_for_timeout(2000)

                    # Estrai link prodotto
                    # Spesso hanno classe .product-item-link o simili
                    links = await page.evaluate('''() => {
                        const anchors = Array.from(document.querySelectorAll('a'));
                        return anchors
                            .map(a => a.href)
                            .filter(href => {
                                // Filtra link che sembrano prodotti
                                // In Grepool spesso hanno diverse sottocartelle
                                return href.includes('/it/') && 
                                       (href.includes('/piscine-') || href.includes('/pulitori-') || href.includes('/filtri/')) &&
                                       !href.includes('/category/') && !href.includes('?q=') && !href.includes('#');
                            });
                    }''')
                    
                    for l in links:
                        all_links.add(l)

                    # Cerca pulsante "Avanti" o paginazione
                    next_page = await page.evaluate('''() => {
                        const next = document.querySelector('a.next, a[rel="next"]');
                        return next ? next.href : null;
                    }''')
                    
                    if next_page and next_page != current_url:
                        current_url = next_page
                    else:
                        current_url = None

                except Exception as e:
                    print(f"   ❌ Errore su {current_url}: {e}")
                    current_url = None

            print(f"   ✨ Totale link trovati finora: {len(all_links)}")
            # Salvataggio incrementale
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(list(all_links), f, indent=4)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_gre_links())
