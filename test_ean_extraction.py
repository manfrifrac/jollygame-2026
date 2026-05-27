import requests
from bs4 import BeautifulSoup
import json
import re

def test_extract_ean(url):
    print(f"\nTesting URL: {url}")
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        ean_found = False
        
        # 1. Check JSON-LD (schema.org)
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                # Sometimes it's a list, sometimes a dict
                if isinstance(data, list):
                    for item in data:
                        if '@type' in item and item['@type'] == 'Product':
                            if 'gtin13' in item:
                                print(f"Found EAN in JSON-LD (gtin13): {item['gtin13']}")
                                ean_found = True
                            elif 'gtin8' in item:
                                print(f"Found EAN in JSON-LD (gtin8): {item['gtin8']}")
                                ean_found = True
                            elif 'sku' in item and len(str(item['sku'])) == 13 and str(item['sku']).isdigit():
                                print(f"Found 13-digit SKU in JSON-LD (potential EAN): {item['sku']}")
                                ean_found = True
                elif isinstance(data, dict):
                    if '@graph' in data:
                        for item in data['@graph']:
                            if item.get('@type') == 'Product':
                                if 'gtin13' in item:
                                    print(f"Found EAN in JSON-LD Graph (gtin13): {item['gtin13']}")
                                    ean_found = True
                                elif 'gtin8' in item:
                                    print(f"Found EAN in JSON-LD Graph (gtin8): {item['gtin8']}")
                                    ean_found = True
                    elif data.get('@type') == 'Product':
                        if 'gtin13' in data:
                            print(f"Found EAN in JSON-LD (gtin13): {data['gtin13']}")
                            ean_found = True
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                pass
                
        # 2. Check meta tags
        if not ean_found:
            gtin_meta = soup.find('meta', attrs={'property': 'product:gtin13'})
            if gtin_meta and gtin_meta.get('content'):
                print(f"Found EAN in meta tag: {gtin_meta['content']}")
                ean_found = True
                
        # 3. Check for specific WooCommerce/Prestashop hidden fields
        if not ean_found:
            ean_span = soup.find('span', class_='ean')
            if ean_span:
                print(f"Found EAN in span.ean: {ean_span.text.strip()}")
                ean_found = True
                
        # 4. Regex fallback in raw HTML
        if not ean_found:
            matches = re.findall(r'"gtin13"\s*:\s*"(\d{13})"', response.text)
            if matches:
                print(f"Found EAN via regex (gtin13): {matches[0]}")
                ean_found = True
            else:
                 matches = re.findall(r'ean.*?(\d{13})', response.text, re.IGNORECASE)
                 if matches:
                     print(f"Found EAN via regex (ean...): {matches[0]}")
                     ean_found = True
                     
        if not ean_found:
            print("No EAN/GTIN found in the page source.")
            
    except Exception as e:
        print(f"Error fetching URL: {e}")

if __name__ == "__main__":
    test_urls = [
        "https://www.intexitalia.com/altalene-swing-set/altalena-colorata-con-set-di-gioco-a-5-funzioni/",
        "https://www.intexricambi.it/ricambi/liner-per-piscina-easy-set-305x61-cm/",
        "https://www.intexitalia.com/pompe-e-gonfiatori/pompa-elettrica-quickfill-220-240-v-e-12-v-2/"
    ]
    for url in test_urls:
        test_extract_ean(url)
