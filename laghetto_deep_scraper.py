import asyncio
import json
import csv
import os
import random
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

class LaghettoScraper:
    def __init__(self):
        self.base_url = "https://www.piscinelaghetto.com"
        self.output_file = "laghetto_full_export_enriched.csv"
        self.links_file = "laghetto_links.json"
        
        with open(self.links_file, 'r') as f:
            self.links = json.load(f)

    async def get_page_content(self, page, url):
        print(f"Navigating to: {url}")
        for attempt in range(2):
            try:
                await asyncio.sleep(random.uniform(2, 4))
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)
                # Scroll to load lazy content
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                await page.wait_for_timeout(1000)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                return await page.content()
            except Exception as e:
                print(f"Attempt {attempt+1} failed for {url}: {e}")
                await page.wait_for_timeout(5000)
        return None

    def parse_product(self, html, url):
        soup = BeautifulSoup(html, 'lxml')
        
        # Title
        title = ""
        title_tag = soup.select_one(".pool-name-label")
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            h1 = soup.select_one("h1")
            if h1: title = h1.get_text(strip=True)

        # Technical Sections (Narrative)
        details = []
        sections = soup.select(".product__detail")
        for section in sections:
            sec_title_tag = section.select_one(".product__title")
            sec_content_tag = section.select_one(".product__content")
            if sec_title_tag and sec_content_tag:
                sec_title = sec_title_tag.get_text(strip=True)
                sec_text = sec_content_tag.get_text(strip=True)
                details.append(f"### {sec_title}\n{sec_text}")

        # Data Sheet (Table/Lists)
        technical_data = []
        datasheet = soup.select_one(".product__datasheet-container")
        if datasheet:
            # Look for labels and values
            items = datasheet.select(".datasheet__item") # Hypothetical selector based on typical theme
            if not items:
                # Try generic list items or spans inside the datasheet container
                items = datasheet.find_all(['li', 'div'], class_=lambda x: x and 'item' in x)
            
            for item in items:
                text = item.get_text(separator=': ', strip=True)
                if text: technical_data.append(text)
            
            if not technical_data:
                # Just take the text of the whole container if structure is messy
                technical_data.append(datasheet.get_text(separator='\n', strip=True))

        # Maintenance
        maintenance = []
        m_titles = soup.select(".maintenance__title")
        m_bodies = soup.select(".maintenance__body")
        for t, b in zip(m_titles, m_bodies):
            maintenance.append(f"### {t.get_text(strip=True)}\n{b.get_text(strip=True)}")

        # PDF Links
        pdfs = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.lower().endswith('.pdf'):
                label = a.get_text(strip=True) or "Documento PDF"
                pdfs.append(f"{label}|{href}")
        
        # YouTube Links
        videos = []
        # Check iframes
        iframes = soup.find_all('iframe', src=True)
        for iframe in iframes:
            src = iframe['src']
            if 'youtube.com' in src or 'youtu.be' in src:
                videos.append(src)
        # Check links
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'youtube.com/watch' in href or 'youtu.be/' in href:
                videos.append(href)

        # Images
        images = []
        img_tags = soup.select(".product__promoted-image img, .product__gallery-wrapper img")
        for img in img_tags:
            src = img.get('data-src') or img.get('src')
            if src and not src.startswith('data:'):
                images.append(src)
        
        images = list(set(images))

        data = {
            "URL": url,
            "Titolo": title,
            "Caratteristiche_Tecniche": "\n\n".join(details),
            "Scheda_Tecnica_Dati": "\n".join(technical_data),
            "Descrizione_Manutenzione": "\n\n".join(maintenance),
            "PDF_Documenti": "; ".join(list(set(pdfs))),
            "Video_YouTube": "; ".join(list(set(videos))),
            "Immagini": ";".join(images),
            "Tags": "Piscine Laghetto"
        }
        return data

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            await Stealth().apply_stealth_async(page)

            fieldnames = ["URL", "Titolo", "Caratteristiche_Tecniche", "Scheda_Tecnica_Dati", "Descrizione_Manutenzione", "PDF_Documenti", "Video_YouTube", "Immagini", "Tags"]
            
            with open(self.output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for url in self.links:
                    html = await self.get_page_content(page, url)
                    if html:
                        product_data = self.parse_product(html, url)
                        writer.writerow(product_data)
                        print(f"Saved: {product_data['Titolo']}")
                    else:
                        print(f"Failed to get content for {url}")
            
            await browser.close()
            print(f"Scraping complete. Data saved to {self.output_file}")

if __name__ == "__main__":
    scraper = LaghettoScraper()
    asyncio.run(scraper.run())
