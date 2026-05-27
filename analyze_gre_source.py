from bs4 import BeautifulSoup
import re
import json

def analyze_source():
    try:
        with open('debug_gre_source.html', 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')
        
        # 1. Extract DAM links
        links = re.findall(r'https://dam\.fluidra\.com/m/[0-9a-fA-F]+/[^\s\"\'\)]+\.jpg', str(soup))
        links = list(set(links))
        print(f"Total Unique DAM Links: {len(links)}")
        for l in links[:5]:
            print(f"  - {l}")
            
        # 2. Look for the main product data (SKU)
        # Search for "Ref." or similar
        content = soup.get_text()
        sku_match = re.search(r'Rif\.:?\s*([A-Z0-9]+)', content)
        if sku_match:
            print(f"Main SKU in file: {sku_match.group(1)}")
            
        # 3. Look for gallery configuration
        # Often Magento has [data-gallery-role=gallery-placeholder]
        gallery_config = soup.find('script', type='text/x-magento-init')
        if gallery_config:
            print("Found Magento Init script.")
            # Search specifically for gallery in its text
            if 'mage/gallery/gallery' in gallery_config.string:
                print("  Contains gallery config!")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_source()
