
import shopify
import urllib.parse
import time

# CREDENZIALI
SHOP_URL = "jollygamepiscine.myshopify.com"
API_KEY = "3b1522894ce78d0f28f711abda547b3d"
API_SECRET = "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"
API_VERSION = "2026-04"
SCOPES = ['write_content', 'read_content']

def get_path(url):
    if not isinstance(url, str) or not url.startswith("http"):
        return None
    return urllib.parse.urlparse(url).path

def run_test(token):
    session = shopify.Session(SHOP_URL, API_VERSION, token)
    shopify.ShopifyResource.activate_session(session)
    
    # DATI DI TEST FORNITI
    test_cases = [
        {
            "sku": "790000",
            "old": "https://jollygame.it/piscina-quadrata-in-legno-gre-city-225x225x65-cm-790000.html",
            "new": "https://jollygame.it/products/piscine-in-legno-quadrata-city-225-x-225-x-68-cm"
        },
        {
            "sku": "790207",
            "old": "https://jollygame.it/piscine-gre-montaggio-prezzi-fuoriterra-alta-dimensioni-rotonda-ovale-costo-prezzo-giardino-bassa/piscina-fuori-terra-in-legno-rettangolare-braga-790207-gre-sunbay-travi-metalliche-pino.html",
            "new": "https://jollygame.it/products/piscine-in-legno-rettangolare-marbella-2-420-x-270-x-117cm"
        }
    ]
    
    print(f"\nInizio Test Redirect su {SHOP_URL}...")
    
    for item in test_cases:
        path_from = get_path(item["old"])
        path_to = get_path(item["new"])
        
        print(f"\n[SKU {item['sku']}] Provando: {path_from} -> {path_to}")
        try:
            redirect = shopify.Redirect.create({
                "path": path_from,
                "target": path_to
            })
            if redirect.errors:
                print(f"  [ERRORE] {redirect.errors.full_messages()}")
            else:
                print(f"  [OK] Redirect creato con successo!")
        except Exception as e:
            print(f"  [ECCEZIONE] {e}")
        time.sleep(1)

if __name__ == "__main__":
    shopify.Session.setup(api_key=API_KEY, secret=API_SECRET)
    session = shopify.Session(SHOP_URL, API_VERSION)
    auth_url = session.create_permission_url(SCOPES, "https://localhost")

    print("="*60)
    print("TEST REDIRECT MANUALI")
    print("="*60)
    print(f"1. Apri questo URL: {auth_url}")
    print("2. Autorizza e copia il codice (o l'intero URL) dalla barra degli indirizzi.")
    print("="*60)

    code_input = input("\nIncolla qui il codice o l'URL: ").strip()
    code = code_input.split("code=")[1].split("&")[0] if "code=" in code_input else code_input

    try:
        access_token = session.request_token({"code": code})
        run_test(access_token)
    except Exception as e:
        print(f"Errore: {e}")
