import asyncio
import csv
import json
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def extract_videos():
    # Read the Zodiac products that have the fake vicQ thumbnail
    products = []
    with open('zodiac_enriched_data.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'vicQ' in row.get('Immagini', ''):
                products.append({
                    'Titolo': row['Titolo'],
                    'URL': row['URL']
                })
    
    print(f"Trovati {len(products)} prodotti Zodiac con video nascosti.")
    video_map = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for prod in products:
            print(f"Scraping: {prod['Titolo']}...")
            try:
                await page.goto(prod['URL'], wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(2000)
                soup = BeautifulSoup(await page.content(), 'lxml')
                
                gallery_imgs = soup.select(".gallery__carousel img")
                found = False
                for img in gallery_imgs:
                    data_video = img.get('data-video')
                    if data_video and 'youtube' in data_video.lower():
                        video_map[prod['Titolo']] = data_video
                        print(f"  => Trovato: {data_video}")
                        found = True
                        break
                if not found:
                    print("  => Nessun video trovato nell'attributo data-video.")
            except Exception as e:
                print(f"  => Errore: {e}")
                
        await browser.close()
        
    with open('zodiac_hidden_videos.json', 'w', encoding='utf-8') as f:
        json.dump(video_map, f, indent=4)
        
    print("Salvataggio completato in zodiac_hidden_videos.json")

if __name__ == "__main__":
    asyncio.run(extract_videos())
