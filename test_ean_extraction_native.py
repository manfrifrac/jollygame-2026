import urllib.request
import re
import json

def test_extract_ean_native(url):
    print(f"\nTesting URL: {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
        ean_found = False
        
        # 1. Regex for gtin13 in the raw HTML
        matches = re.findall(r'"gtin13"\s*:\s*"(\d{13})"', html)
        if matches:
            print(f"Found EAN via regex (gtin13): {matches[0]}")
            ean_found = True
            
        # 2. Regex for product:gtin13 meta tag
        if not ean_found:
            matches = re.findall(r'property="product:gtin13"\s+content="(\d{13})"', html)
            if matches:
                print(f"Found EAN via regex (meta property product:gtin13): {matches[0]}")
                ean_found = True
                
        # 3. Regex for gtin8 in the raw HTML
        if not ean_found:
             matches = re.findall(r'"gtin8"\s*:\s*"(\d{8})"', html)
             if matches:
                 print(f"Found EAN via regex (gtin8): {matches[0]}")
                 ean_found = True
                 
        # 4. Fallback: Search for any 13-digit number that might be EAN
        if not ean_found:
             # Find sequences of exactly 13 digits not surrounded by other digits
             potential_eans = re.findall(r'(?<!\d)(\d{13})(?!\d)', html)
             # Filter out common false positives like timestamps
             filtered_eans = [e for e in potential_eans if not e.startswith('16') and not e.startswith('17')]
             if filtered_eans:
                 # Print unique potentials
                 unique_eans = list(set(filtered_eans))
                 print(f"Potential EANs found (13-digit numbers): {unique_eans}")
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
        test_extract_ean_native(url)
