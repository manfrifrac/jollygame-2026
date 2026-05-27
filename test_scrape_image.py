import asyncio
from playwright.async_api import async_playwright
import sys

USER = "jollygam@libero.it"
PASS = "AntoRiky61"

async def test_fluidra(sku):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("🔑 Login su Fluidra...")
        await page.goto("https://pro.fluidra.com/it_it/customer/account/login/")
        
        try:
            await page.wait_for_selector("input#email", timeout=15000)
            await page.fill("input#email", USER)
            await page.fill("input#pass", PASS)
            await page.click("button.login")
            print("⏳ Attesa del caricamento dashboard...")
            await page.wait_for_url("**/customer/account/", timeout=15000)
            print("✅ Login riuscito!")
        except Exception as e:
            print(f"❌ Login fallito: {e}")
            await browser.close()
            return

        search_url = f"https://pro.fluidra.com/it_it/catalogsearch/result/?q={sku}"
        print(f"🔎 Cerco lo SKU: {sku}")
        await page.goto(search_url)
        await asyncio.sleep(5)
        
        print("Cerco l'immagine...")
        image_url = None
        try:
            # Immagine principale o nella lista
            img_element = page.locator("img.product-image-photo").first
            await img_element.wait_for(timeout=5000)
            image_url = await img_element.get_attribute("src")
        except:
            pass

        if image_url and "placeholder" not in image_url:
            print(f"✅ Immagine trovata: {image_url}")
        else:
            print("❌ Nessuna immagine trovata (nemmeno loggato).")

        await browser.close()

if __name__ == "__main__":
    sku = sys.argv[1] if len(sys.argv) > 1 else "R0516700"
    asyncio.run(test_fluidra(sku))
