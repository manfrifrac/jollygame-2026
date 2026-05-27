import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import re

async def test_image_capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Query pulita: Marca + SKU + Tipo Prodotto
        sku = "KITPROV7388N"
        query = f"Gre {sku} piscina ovale"
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch"
        
        print(f"🚀 Test ricerca per: {query}")
        print(f"🔗 URL: {url}")
        
        try:
            await page.goto(url, wait_until="load")
            await page.wait_for_timeout(3000)
            
            # 1. Gestione Consenso Google (Cruciale)
            if "consent.google" in page.url:
                print("🖱️ Superamento blocco consenso...")
                btn = page.locator("button:has-text('Accetto tutto'), button:has-text('Accept all')").first
                if await btn.count() > 0:
                    await btn.click()
                    await page.wait_for_timeout(2000)

            # 2. Screenshot per vedere cosa vede lo script
            await page.screenshot(path="debug_google_view.png")
            print("📸 Screenshot salvato: debug_google_view.png")

            # 3. Estrazione link con selettori multipli (Google cambia classi spesso)
            images = await page.evaluate('''() => {
                const results = [];
                // Cerca tutti i tag img e i loro contenitori che hanno attributi data-src o src
                document.querySelectorAll('img').forEach(img => {
                    const src = img.src || img.dataset.src || img.dataset.iurl;
                    if (src && src.startsWith('http') && !src.includes('gstatic.com') && img.width > 50) {
                        results.push({
                            src: src,
                            alt: img.alt,
                            width: img.width,
                            height: img.height
                        });
                    }
                });
                return results;
            }''')
            
            print(f"✅ Trovate {len(images)} potenziali immagini.")
            for i, img in enumerate(images[:5]):
                print(f"   [{i+1}] {img['src'][:80]}... ({img['width']}x{img['height']})")
                
        except Exception as e:
            print(f"❌ Errore durante il test: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_image_capture())
