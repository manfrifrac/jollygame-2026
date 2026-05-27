import asyncio
import json
import csv
import os
import random
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

class ZodiacDeepScraper:
    def __init__(self):
        self.base_url = "https://www.zodiac-poolcare.it"
        self.visited = set()
        self.results = []
        # Carica risultati esistenti per la ripresa
        self.output_file = "zodiac_full_export.csv"
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.results.append(row)
                        # Normalizza l'URL per il set dei visitati
                        v_url = row['URL'].split('#')[0].rstrip('/')
                        self.visited.add(v_url)
                print(f"--- Ripresa: {len(self.results)} prodotti già nel database ---")
            except Exception as e:
                print(f"Errore lettura CSV esistente: {e}")

        # Categorie di partenza
        self.categories = [
            "/robot-pulitori",
            "/riscaldamento",
            "/apparecchiature-di-filtrazione",
            "/trattamento-dell-acqua",
            "/deumidificazione",
            "/analisi-dell-acqua"
        ]

    async def get_page_content(self, page, url):
        """Naviga e gestisce i blocchi Incapsula in modo più umano."""
        print(f"\nNavigazione: {url}")
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Delay casuale prima di ogni click per simulare lettura
                await asyncio.sleep(random.uniform(3, 6))
                
                await page.goto(url, wait_until="load", timeout=60000)
                await page.wait_for_timeout(2000)
                
                content = await page.content()
                
                # Verifica blocco Access Denied
                if "Access denied" in content or "Error 17" in content or "#main-iframe" in content:
                    print(f"!!! Blocco rilevato. Aspetto che Incapsula si calmi (15s)...")
                    await page.wait_for_timeout(15000)
                    continue 
                
                # Simula scroll umano
                await page.mouse.wheel(0, random.randint(400, 800))
                await page.wait_for_timeout(1000)
                
                return content
            except Exception as e:
                print(f"Errore caricamento tentativo {attempt+1}: {e}")
                await page.wait_for_timeout(5000)
        return None

    async def extract_links(self, html):
        """Estrae link a sottolivelli usando BS4 per velocità."""
        soup = BeautifulSoup(html, 'lxml')
        links = []
        # Lista nera per evitare social e siti esterni
        blacklist = ["facebook.com", "twitter.com", "linkedin.com", "youtube.com", "instagram.com", "sharer.php"]
        
        for a in soup.find_all('a', href=True):
            href = a['href'].split('#')[0].rstrip('/')
            if not href: continue
            
            # Trasforma in URL assoluto
            if href.startswith('/'):
                href = self.base_url + href
            
            # Deve iniziare con la base_url e non essere in blacklist
            if href.startswith(self.base_url):
                if not any(social in href.lower() for social in blacklist):
                    if href not in self.visited:
                        # Escludi pagine di servizio
                        if not any(x in href for x in ["/circa-noi", "/assistenza", "/soluzioni", "/avvertenze-legali", "cookies", "privacy", "contatti"]):
                            links.append(href)
        return list(set(links))

    async def scrape_product(self, html, url):
        """Estrae i dati finali del prodotto."""
        soup = BeautifulSoup(html, 'lxml')
        title_tag = soup.select_one(".product-info__variantBlock--title")
        if not title_tag:
            return None

        data = {
            "URL": url,
            "Titolo": title_tag.get_text(strip=True),
            "Sottotitolo": soup.select_one(".product-info__variantBlock--category").get_text(strip=True) if soup.select_one(".product-info__variantBlock--category") else "",
            "Prezzo": "",
            "Caratteristiche": "\n".join([li.get_text(strip=True) for li in soup.select(".product-info__variantBlock--list li")]),
            "Descrizione_HTML": str(soup.select_one(".productTab__container.description")) if soup.select_one(".productTab__container.description") else "",
            "Immagini": ";".join(list(set([img['src'] for img in soup.select(".gallery__carousel img") if img.has_attr('src')]))),
            "Tags": ",".join([s.get_text(strip=True) for s in soup.select(".product-breadcrumb__links a span") if "Prodotti" not in s.get_text()])
        }
        
        price_tag = soup.select_one(".product-info__variantBlock--price span")
        if price_tag:
            data["Prezzo"] = price_tag.get_text(strip=True).replace(".", "").replace(",", ".")
            
        return data

    async def run(self):
        async with async_playwright() as p:
            # Nuova sessione per il nuovo IP VPN
            user_data_dir = os.path.join(os.getcwd(), "zodiac_session_vpn")
            
            # Configurazione Proxy Mullvad SOCKS5 (standard per Mullvad attivo)
            proxy_settings = {
                "server": "socks5://10.64.0.1:1080"
            }
            
            print(f"--- FASE 1: Avvio con VPN Mullvad ---")
            try:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir,
                    headless=False,
                    proxy=proxy_settings,
                    args=["--disable-blink-features=AutomationControlled"],
                    slow_mo=200,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
                )
            except Exception as e:
                print(f"Tentativo con proxy fallito, provo senza: {e}")
                context = await p.chromium.launch_persistent_context(
                    user_data_dir,
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"],
                    slow_mo=200
                )
            
            page = context.pages[0]
            await Stealth().apply_stealth_async(page)

            await page.goto(self.base_url)
            print("Verifica l'accesso. Avvio tra 10 secondi...")
            await page.wait_for_timeout(10000)

            queue = [self.base_url + c for c in self.categories]
            
            while queue:
                url = queue.pop(0)
                if url in self.visited: continue
                # Non aggiungiamo ai visitati qui, lo faremo solo se il caricamento ha successo
                
                html = await self.get_page_content(page, url)
                if not html: continue
                
                self.visited.add(url) # Ora è visitata con successo

                soup = BeautifulSoup(html, 'lxml')
                body = soup.find('body')
                classes = body.get('class', []) if body else []
                
                # Se è un prodotto
                if "page-product" in " ".join(classes):
                    product = await self.scrape_product(html, url)
                    if product:
                        print(f"PRODOTTO TROVATO: {product['Titolo']}")
                        self.results.append(product)
                        self.save()
                
                # Cerca nuovi link a sottolivelli o altri prodotti
                new_links = await self.extract_links(html)
                for nl in new_links:
                    if nl not in self.visited and nl not in queue:
                        queue.append(nl)
                
                print(f"Stato: {len(self.results)} prodotti salvati. Link da visitare: {len(queue)}")

            await browser_context.close()

    def save(self):
        if not self.results: return
        keys = self.results[0].keys()
        with open(self.output_file, "w", newline="", encoding="utf-8") as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(self.results)

if __name__ == "__main__":
    scraper = ZodiacDeepScraper()
    asyncio.run(scraper.run())
