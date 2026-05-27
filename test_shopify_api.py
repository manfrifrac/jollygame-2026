
import shopify
import urllib.parse
import time

# CONFIGURAZIONE SHOPIFY
SHOP_URL = "jollygamepiscine.myshopify.com"
ACCESS_TOKEN = "shptka_56c35907b97a4928db981b5c8f926324"

# Inizializza Shopify
shopify.ShopifyResource.set_site(f"https://{SHOP_URL}/admin/api/2024-01")
shopify.ShopifyResource.set_headers({"X-Shopify-Access-Token": ACCESS_TOKEN})

def get_path(url):
    """Estrae solo il path da un URL"""
    if not isinstance(url, str) or not url.startswith("http"):
        return None
    path = urllib.parse.urlparse(url).path
    return path

def test_redirects():
    test_data = [
        {
            "old": "https://jollygame.it/piscine-gre-montaggio-prezzi-fuoriterra-alta-dimensioni-rotonda-ovale-costo-prezzo-giardino-bassa/piscina-fuori-terra-in-legno-rettangolare-braga-790207-gre-sunbay-travi-metalliche-pino.html",
            "new": "https://jollygame.it/products/piscine-in-legno-rettangolare-marbella-2-420-x-270-x-117cm" # Preso dal CSV per lo SKU 790207
        },
        {
            "old": "https://jollygame.it/piscina-fuori-terra-in-legno-rettangolare-evora-790206-gre-sunbay-travi-metalliche-pino.html",
            "new": "https://jollygame.it/products/piscine-in-legno-rettangolare-marbella-2-420-x-270-x-117cm" # Esempio di fallback se non trovato
        }
    ]
    
    for item in test_data:
        path_from = get_path(item["old"])
        path_to = get_path(item["new"])
        
        print(f"Tentativo redirect: {path_from} -> {path_to}")
        try:
            new_redirect = shopify.Redirect.create({
                "path": path_from,
                "target": path_to
            })
            if new_redirect.errors:
                print(f"  [ERRORE] {new_redirect.errors.full_messages()}")
            else:
                print(f"  [OK] Creato con successo!")
        except Exception as e:
            print(f"  [ERRORE] Eccezione: {e}")
        time.sleep(1)

if __name__ == "__main__":
    test_redirects()
