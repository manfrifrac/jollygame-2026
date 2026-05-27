import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json

async def get_gre_categories():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        
        print("🚀 Recupero categorie da Grepool...")
        await page.goto("https://www.grepool.com/it", wait_until="networkidle")
        
        # Cerca link nel menu
        categories = await page.evaluate('''() => {
            const links = Array.from(document.querySelectorAll('nav a, .menu a, .category-list a, .footer a'));
            return links
                .map(a => ({ label: a.innerText.trim(), url: a.href }))
                .filter(c => c.url.includes('/it/') && c.label.length > 3 && !c.url.includes('#'));
        }''')
        
        unique_cats = []
        seen = set()
        for c in categories:
            if c['url'] not in seen:
                seen.add(c['url'])
                unique_cats.append(c)

        print(f"✅ Trovate {len(unique_cats)} categorie.")
        with open("gre_categories.json", "w", encoding="utf-8") as f:
            json.dump(unique_cats, f, indent=4, ensure_ascii=False)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_gre_categories())
