import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def find_image_web():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Cerchiamo su Google Web, non immagini
        sku = "KITPROV7388N"
        query = f"Gre {sku} piscina ovale"
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        
        print(f"🚀 Ricerca WEB per: {query}")
        
        try:
            await page.goto(url, wait_until="load")
            await page.wait_for_timeout(2000)
            
            if "consent.google" in page.url:
                btn = page.locator("button:has-text('Accetto tutto')").first
                if await btn.count() > 0: await btn.click()
                await page.wait_for_timeout(2000)

            # Cerca il primo risultato che non sia pubblicità
            # Spesso i risultati hanno tag <a> con l'URL
            links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a'))
                    .map(a => a.href)
                    .filter(h => h.includes('grepool.com') || h.includes('sanmarcopiscine') || h.includes('manomano'));
            }''')
            
            if links:
                target_url = links[0]
                print(f"✅ Trovato link utile: {target_url}")
                
                # Naviga nel link trovato per prendere la foto
                await page.goto(target_url, wait_until="networkidle")
                await page.wait_for_timeout(3000)
                
                # Estrai l'immagine principale
                img_src = await page.evaluate('''() => {
                    // Selettori comuni per immagini principali
                    const img = document.querySelector('.product-image-main img, .main-image img, #main-image, [itemprop="image"]');
                    return img ? img.src : null;
                }''')
                
                if img_src:
                    print(f"✨ IMMAGINE TROVATA: {img_src}")
                else:
                    print("❌ Nessuna immagine chiara nel link di destinazione.")
            else:
                print("❌ Nessun link Grepool/SanMarco trovato nei risultati Google.")

        except Exception as e:
            print(f"❌ Errore: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(find_image_web())
