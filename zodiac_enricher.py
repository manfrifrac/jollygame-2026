import asyncio
import json
import csv
import os
import random
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

class ZodiacEnricher:
    def __init__(self):
        self.base_url = "https://www.zodiac-poolcare.it"
        self.input_file = "zodiac_full_export.csv"
        self.output_file = "zodiac_enriched_data.csv"
        self.products_to_process = []
        
        # Carica i prodotti dal CSV precedente
        if os.path.exists(self.input_file):
            try:
                with open(self.input_file, mode='r', encoding='utf-8') as f:
                    self.products_to_process = list(csv.DictReader(f))
                print(f"Caricati {len(self.products_to_process)} prodotti da arricchire.")
            except Exception as e:
                print(f"Errore caricamento CSV: {e}")
        else:
            print("File zodiac_full_export.csv non trovato!")

    async def get_deep_data(self, page, url):
        """Estrae PDF, Prezzi nascosti e Video."""
        print(f"\nAnalisi profonda: {url}")
        try:
            # Delay casuale per simulare umano
            await asyncio.sleep(random.uniform(2, 4))
            
            await page.goto(url, wait_until="load", timeout=60000)
            await page.wait_for_timeout(2000)
            
            # Scorriamo per caricare eventuali elementi lazy
            await page.mouse.wheel(0, 1200)
            await page.wait_for_timeout(1000)

            html = await page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # 1. Ricerca Prezzo (anche nei metadati JSON-LD)
            price = ""
            price_tag = soup.select_one(".product-info__variantBlock--price span")
            if price_tag:
                price = price_tag.get_text(strip=True).replace(".", "").replace(",", ".")
            
            # Ricerca profonda nel JSON-LD
            json_ld_tags = soup.find_all('script', type='application/ld+json')
            for tag in json_ld_tags:
                try:
                    data = json.loads(tag.string)
                    # Gestione sia di dict che di list di dict
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if 'offers' in item:
                            p = item['offers'].get('price')
                            if p: price = str(p)
                            break
                        if item.get('@type') == 'Product' and 'offers' in item:
                            p = item['offers'].get('price')
                            if p: price = str(p)
                            break
                except: continue

            # 2. Estrazione PDF (Manuali, Guide, Depliant)
            pdf_links = []
            download_section = soup.select(".productTab__container.downloads ul li")
            for item in download_section:
                title_tag = item.select_one(".mediaType-title")
                link_tag = item.select_one("a[href*='.pdf']")
                if title_tag and link_tag:
                    name = title_tag.get_text(strip=True)
                    link = link_tag['href']
                    pdf_links.append(f"{name}|{link}")
            
            # 3. Estrazione Video YouTube
            youtube_links = []
            videos = soup.find_all(['iframe', 'source', 'video'])
            for v in videos:
                src = v.get('src') or v.get('data-video') or v.get('data-cookieblock-src')
                if src and 'youtube' in src:
                    if src.startswith('//'): src = 'https:' + src
                    youtube_links.append(src)

            return {
                "Enriched_Price": price,
                "PDF_Links": "; ".join(pdf_links),
                "YouTube_Videos": "; ".join(list(set(youtube_links)))
            }

        except Exception as e:
            print(f"Errore su {url}: {e}")
            return None

    async def run(self):
        async with async_playwright() as p:
            user_data_dir = os.path.join(os.getcwd(), "zodiac_session_enricher")
            proxy_settings = {"server": "socks5://10.64.0.1:1080"}
            
            try:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir,
                    headless=False,
                    proxy=proxy_settings,
                    args=["--disable-blink-features=AutomationControlled"],
                    slow_mo=200,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
                )
            except:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir,
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"],
                    slow_mo=200
                )
            
            page = context.pages[0]
            await Stealth().apply_stealth_async(page)
            
            # Check iniziale
            await page.goto(self.base_url)
            await page.wait_for_timeout(5000)

            results = []
            for i, prod in enumerate(self.products_to_process):
                deep_data = await self.get_deep_data(page, prod['URL'])
                
                enriched_prod = prod.copy()
                if deep_data:
                    # Aggiorna prezzo solo se vuoto o se trovato uno nuovo
                    if not enriched_prod.get('Prezzo') or enriched_prod['Prezzo'] == '' or enriched_prod['Prezzo'] == '0':
                        enriched_prod['Prezzo'] = deep_data['Enriched_Price']
                    
                    enriched_prod['PDF_Documents'] = deep_data['PDF_Links']
                    enriched_prod['YouTube_Videos'] = deep_data['YouTube_Videos']
                
                results.append(enriched_prod)
                
                if (i + 1) % 5 == 0:
                    self.save(results)
                
                print(f"Avanzamento: {i+1}/{len(self.products_to_process)} prodotti arricchiti.")

            self.save(results)
            await context.close()
            print(f"\n--- ARRICCHIMENTO COMPLETATO ---")
            print(f"Dati salvati in: {self.output_file}")

    def save(self, data):
        if not data: return
        keys = data[0].keys()
        with open(self.output_file, "w", newline="", encoding="utf-8") as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)

if __name__ == "__main__":
    enricher = ZodiacEnricher()
    asyncio.run(enricher.run())
