import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def check_videos(url, name):
    print(f"\n--- Checking {name} ---")
    print(f"URL: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000) # wait for dynamic content
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
            await page.wait_for_timeout(2000)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)

            content = await page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            print("Searching for iframes...")
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src') or iframe.get('data-src') or iframe.get('data-cookieblock-src')
                print(f"Iframe found: src={src}")
                
            print("Searching for youtube links in <a> tags...")
            a_tags = soup.find_all('a', href=True)
            for a in a_tags:
                href = a['href']
                if 'youtube.com' in href or 'youtu.be' in href:
                    print(f"Link found: {href}")

            print("Searching for raw video tags or placeholders...")
            videos = soup.find_all('video')
            for v in videos:
                print(f"Video tag found: src={v.get('src')}")
                
            divs_with_video = soup.select('[class*="video"], [id*="video"]')
            print(f"Found {len(divs_with_video)} elements with 'video' in class or id.")
            for d in divs_with_video[:3]:
                if 'youtube' in str(d):
                    print("Contains youtube reference.")
                
        except Exception as e:
            print(f"Error checking {name}: {e}")
        finally:
            await browser.close()

async def main():
    zodiac_url = "https://www.zodiac-poolcare.it/robot-pulitori/robot-elettrici-per-piscine-residenziali/gamma-alpha-iq-/ra-6300-iq"
    laghetto_url = "https://www.piscinelaghetto.com/product/minipiscine/musa-picnic"
    
    await check_videos(zodiac_url, "Zodiac RA 6300 iQ")
    await check_videos(laghetto_url, "Laghetto Ninfea Thiny (Musa Picnic)")

if __name__ == "__main__":
    asyncio.run(main())
