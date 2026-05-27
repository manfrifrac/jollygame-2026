import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import re
from bs4 import BeautifulSoup

async def scrape_all_intex_pages():
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse('intex_cat_sitemap.xml')
        root = tree.getroot()
        cat_urls = [loc.text for loc in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    except:
        print("Sitemap non trovata.")
        return

    mapping = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for base_url in cat_urls:
            cat_name = base_url.replace("https://www.intexitalia.com/", "").strip("/")
            mapping[cat_name] = []
            
            current_page_url = base_url
            page_num = 1
            
            while current_page_url:
                print(f"Scraping {cat_name} - Pagina {page_num}...")
                try:
                    await page.goto(current_page_url, wait_until="load", timeout=60000)
                    await asyncio.sleep(3)
                    
                    content = await page.content()
                    soup = BeautifulSoup(content, 'lxml')
                    
                    # Estrazione link prodotti (Logica più permissiva)
                    # Qualsiasi link che ha più di 4 segmenti nel path e inizia con la base del sito
                    found_links = []
                    for a in soup.find_all('a', href=True):
                        href = a['href'].split('?')[0].rstrip('/')
                        if href.startswith('https://www.intexitalia.com') and href != base_url.rstrip('/'):
                            # Un prodotto solitamente ha un URL lungo (es. /cat/sottocat/prodotto/)
                            path_segments = href.replace('https://www.intexitalia.com', '').strip('/').split('/')
                            if len(path_segments) >= 2: # Almeno categoria + prodotto
                                found_links.append(href)
                    
                    mapping[cat_name].extend(found_links)
                    
                    # Cerco il link "Next"
                    next_page = soup.select_one('a.next.page-numbers')
                    if next_page and next_page.get('href'):
                        current_page_url = next_page['href']
                        page_num += 1
                    else:
                        current_page_url = None
                        
                except Exception as e:
                    print(f"   ❌ Errore su {current_page_url}: {e}")
                    current_page_url = None

            mapping[cat_name] = list(set(mapping[cat_name]))
            print(f"   -> Totale prodotti trovati in {cat_name}: {len(mapping[cat_name])}")

        await browser.close()

    with open("intex_url_category_map_v2.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=4)
    
    print("\n✅ Mappatura completa (v2) terminata.")

if __name__ == "__main__":
    asyncio.run(scrape_all_intex_pages())
