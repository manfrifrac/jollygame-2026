import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def find_image_ean():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        
        # EAN per Marbella 2 7900962
        ean = "8412081318448"
        query = f"{ean} Gre pool"
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        
        print(f"🚀 Ricerca WEB via EAN per: {query}")
        
        try:
            await page.goto(url, wait_until="load")
            await page.wait_for_timeout(3000)
            
            if "consent.google" in page.url:
                btn = page.locator("button:has-text('Accetto tutto')").first
                if await btn.count() > 0: await btn.click()
                await page.wait_for_timeout(2000)

            # Cerca link professionali
            links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a'))
                    .map(a => a.href)
                    .filter(h => h.includes('grepool.com') || h.includes('sanmarcopiscine') || h.includes('manomano') || h.includes('poolaria'));
            }''')
            
            if links:
                target_url = links[0]
                print(f"✅ Trovato link via EAN: {target_url}")
                
                await page.goto(target_url, wait_until="networkidle")
                await page.wait_for_timeout(3000)
                
                img_src = await page.evaluate('''() => {
                    const img = document.querySelector('.product-image-main img, .main-image img, #main-image, [itemprop="image"], .gallery__image');
                    return img ? img.src : null;
                }''')
                
                if img_src:
                    print(f"✨ IMMAGINE TROVATA: {img_src}")
                else:
                    print("❌ Nessuna immagine chiara nel link di destinazione.")
            else:
                print("❌ Nessun link utile trovato nei risultati Google per EAN.")

        except Exception as e:
            print(f"❌ Errore: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(find_image_ean())
