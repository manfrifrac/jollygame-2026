import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        # Navighiamo alla pagina di login che poi redirige all'Identity Provider
        await page.goto("https://pro.fluidra.com/it_it/customer/account/login/")
        print("Attendo reindirizzamento...")
        await asyncio.sleep(10)
        content = await page.content()
        with open("new_login_page.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("HTML salvato in new_login_page.html. Chiudi il browser.")
        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
