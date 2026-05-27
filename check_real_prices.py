import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
import re

async def check_public_prices():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        
        targets = [
            # Esempio Gre con widget prezzi
            "https://www.grepool.com/it/piscine-in-acciaio/amazonia-ovale/610-x-375-x-132-cm-3",
            # Esempio AstralPool (Fluidra)
            "https://www.astralpool.com/it/prodotti/piscina-residenziale/pulizia-e-manutenzione-della-piscina/pulitori-elettrici-per-piscine/pulitore-per-piscine-h5-duo/"
        ]
        
        for url in targets:
            print(f"\n🔍 Controllo Prezzo Pubblico: {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(5000) # Aspettiamo il caricamento dei widget esterni
                
                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                # Cerchiamo pattern di prezzo (euro)
                # 1. Cerco testi che contengono il simbolo €
                prices = soup.find_all(string=re.compile(r'\d+[,.]\d+\s*€|€\s*\d+[,.]\d+'))
                if prices:
                    print(f"   💰 Prezzi trovati nel testo: {list(set([p.strip() for p in prices if len(p) < 20]))}")
                
                # 2. Cerco specifici widget (es. PriceSpider, ChannelSight)
                if "channelsight" in content.lower():
                    print("   🔗 Rilevato widget ChannelSight (Dove acquistare).")
                    # Proviamo a estrarre il prezzo dal widget
                    widget_prices = await page.evaluate('''() => {
                        const items = Array.from(document.querySelectorAll('.cs-price, .ps-price, .price'));
                        return items.map(i => i.innerText);
                    }''')
                    print(f"   🛒 Prezzi dal widget: {widget_prices}")

                # 3. Controllo se c'è un MSRP (Prezzo consigliato)
                msrp = soup.find(string=re.compile(r'Prezzo consigliato|MSRP|Retail Price', re.I))
                if msrp:
                    print(f"   📢 Trovato riferimento MSRP: {msrp.parent.get_text(strip=True)}")

            except Exception as e:
                print(f"   ❌ Errore: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_public_prices())
