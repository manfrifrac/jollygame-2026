import json
from bs4 import BeautifulSoup

def parse_html():
    with open("sample_product.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "lxml")
    
    data = {}
    
    # Title
    title_elem = soup.select_one("h1.product_title")
    if title_elem:
        data["title"] = title_elem.get_text(strip=True)
        
    # Price
    price_elem = soup.select_one("p.price .woocommerce-Price-amount bdi")
    if price_elem:
        data["price"] = price_elem.get_text(strip=True)
        
    # SKU
    sku_elem = soup.select_one(".sku")
    if sku_elem:
        data["sku"] = sku_elem.get_text(strip=True)
        
    # EAN
    ean_elem = soup.select_one(".ean") or soup.find(string=lambda t: t and "EAN" in t)
    if ean_elem:
        data["ean"] = ean_elem.parent.get_text(strip=True) if hasattr(ean_elem, "parent") else ean_elem.strip()
        
    # Short description
    short_desc_elem = soup.select_one(".woocommerce-product-details__short-description")
    if short_desc_elem:
        data["short_description"] = short_desc_elem.get_text(separator="\n", strip=True)
        
    # Full description
    desc_elem = soup.select_one("#tab-description")
    if desc_elem:
        data["full_description_length"] = len(desc_elem.get_text(strip=True))
        
    # Images
    images = soup.select(".woocommerce-product-gallery__image a")
    data["images"] = [img.get("href") for img in images if img.get("href")]
    
    # Technical Data (Table)
    tech_table = soup.select_one("table.woocommerce-product-attributes")
    data["attributes"] = {}
    if tech_table:
        rows = tech_table.select("tr")
        for row in rows:
            th = row.select_one("th")
            td = row.select_one("td")
            if th and td:
                data["attributes"][th.get_text(strip=True)] = td.get_text(strip=True)
                
    # Manuals / PDFs
    pdfs = soup.select('a[href$=".pdf"]')
    data["pdfs"] = [pdf.get("href") for pdf in pdfs if pdf.get("href")]
    
    # Other tabs or sections? (Like "Ricambi")
    tabs = soup.select(".wc-tabs li a")
    data["tabs_available"] = [tab.get_text(strip=True) for tab in tabs]
    
    # Categories / Tags
    cats = soup.select(".posted_in a")
    data["categories"] = [cat.get_text(strip=True) for cat in cats]
    
    tags = soup.select(".tagged_as a")
    data["tags"] = [tag.get_text(strip=True) for tag in tags]

    print(json.dumps(data, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    parse_html()
