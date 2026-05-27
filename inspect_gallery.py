import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def inspect_gallery(url):
    print(f"Inspecting gallery at: {url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            gallery = soup.select(".gallery__carousel")
            if not gallery:
                print("Gallery carousel not found.")
            else:
                print(f"Found {len(gallery)} gallery carousels.")
                for g in gallery:
                    items = g.find_all(True)
                    for item in items:
                        if 'youtube' in str(item).lower() or 'video' in str(item).lower() or 'qr' in str(item).lower():
                            print(f"Interesting element: {item.name}")
                            print(item.attrs)
                            
            print("\nLooking for anything with 'qr' in its class, id or src...")
            qr_elements = soup.find_all(lambda tag: any('qr' in str(v).lower() for k, v in tag.attrs.items() if k in ['class', 'id', 'src', 'href']))
            for el in qr_elements[:5]:
                print(f"QR Match: {el.name} -> attrs: {el.attrs}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_gallery("https://www.zodiac-poolcare.it/robot-pulitori/robot-elettrici-per-piscine-residenziali/gamma-alpha-iq-/ra-6300-iq"))
