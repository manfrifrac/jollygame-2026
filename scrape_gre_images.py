import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import json
import urllib.parse

def clean_sku(sku):
    if pd.isna(sku) or str(sku).strip().upper() == 'ARTICOLO':
        return None
    return str(sku).strip()

def search_grepool(sku):
    # Try the search endpoint first
    encoded_sku = urllib.parse.quote(sku)
    url = f"https://www.grepool.com/it/search?q={encoded_sku}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Scenario 1: Search results page
        product_links = soup.select('.product-item a')
        if product_links:
            # Get the first result's URL
            product_url = product_links[0].get('href')
            if not product_url.startswith('http'):
                product_url = 'https://www.grepool.com' + product_url
            return extract_images_from_product_page(product_url, headers)
            
        # Scenario 2: Direct redirect to product page (some sites do this if only 1 exact match)
        if 'search' not in response.url:
             return extract_images_from_product_page(response.url, headers)
             
        # Scenario 3: Try generic product URL pattern if search fails
        # Many Gre products follow: https://www.grepool.com/it/piscine-.../name-of-pool
        # Hard to guess the path, so search is best.
        
        # Let's check for any images on the search results that might be the product
        images = soup.select('.product-item img')
        if images:
             img_urls = []
             for img in images:
                 src = img.get('data-src') or img.get('src')
                 if src:
                     if src.startswith('//'): src = 'https:' + src
                     elif src.startswith('/'): src = 'https://www.grepool.com' + src
                     img_urls.append(src)
             return list(set(img_urls))
             
        return []

    except Exception as e:
        print(f"Error searching {sku}: {e}")
        return []

def extract_images_from_product_page(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        img_urls = []
        
        # Try finding the main gallery
        # This selector depends on the actual HTML structure of grepool.com
        gallery_images = soup.select('.product-gallery img') or soup.select('.fotorama__img') or soup.select('.product-image-photo')
        
        for img in gallery_images:
            src = img.get('data-src') or img.get('src')
            if src:
                # Get highest resolution usually by removing specific size parameters
                # Or just grab what's there
                if src.startswith('//'): src = 'https:' + src
                elif src.startswith('/'): src = 'https://www.grepool.com' + src
                img_urls.append(src)
                
        # If specific selectors fail, grab large images
        if not img_urls:
             all_images = soup.find_all('img')
             for img in all_images:
                 src = img.get('src')
                 if src and ('product' in src.lower() or 'catalog' in src.lower()) and 'media' in src.lower():
                      if src.startswith('//'): src = 'https:' + src
                      elif src.startswith('/'): src = 'https://www.grepool.com' + src
                      img_urls.append(src)
                      
        return list(set(img_urls))
    except Exception as e:
        print(f"Error extracting from {url}: {e}")
        return []


def main():
    df = pd.read_csv('prodotti_gre_mancanti.csv')
    results = {}
    
    # Filter valid SKUs
    skus_to_check = [clean_sku(s) for s in df['sku'].tolist() if clean_sku(s)]
    
    print(f"Starting scrape for {len(skus_to_check)} SKUs...")
    
    # We will test with a small batch first to ensure it works
    test_batch = skus_to_check[:10]
    
    for sku in test_batch:
        print(f"Searching: {sku}")
        images = search_grepool(sku)
        results[sku] = images
        print(f"Found {len(images)} images.")
        time.sleep(random.uniform(1, 3)) # Be polite
        
    with open('gre_images_test.json', 'w') as f:
        json.dump(results, f, indent=4)
        
    print("\nTest completed. Results saved to gre_images_test.json")

if __name__ == "__main__":
    main()
