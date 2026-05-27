from bs4 import BeautifulSoup
import os

if os.path.exists('intex_italia_debug.html'):
    with open('intex_italia_debug.html', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
        links = soup.find_all('a', href=True)
        print(f"Totale link: {len(links)}")
        for a in links:
            href = a['href']
            text = a.get_text(strip=True)
            if "/prodotti/" in href and len(href.split('/')) > 4:
                print(f"CATEGORIA: {text} | {href}")
else:
    print("File non trovato.")
