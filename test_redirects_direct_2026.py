
import requests
import time

# CONFIGURAZIONE SHOPIFY 2026 (Client Credentials Flow)
SHOP_URL = "jollygamepiscine.myshopify.com"
CLIENT_ID = "3b1522894ce78d0f28f711abda547b3d"
CLIENT_SECRET = "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"
API_VERSION = "2026-04"

def get_access_token():
    """Ottiene il token di sessione 2026 tramite Client Credentials."""
    url = f"https://{SHOP_URL}/admin/oauth/access_token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    
    print(f"Richiedo token di accesso per {SHOP_URL}...")
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Errore autenticazione: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Eccezione durante autenticazione: {e}")
        return None

def create_redirect(token, path_from, path_to):
    """Crea il redirect via GraphQL."""
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/graphql.json"
    
    query = """
    mutation urlRedirectCreate($urlRedirect: UrlRedirectInput!) {
      urlRedirectCreate(urlRedirect: $urlRedirect) {
        urlRedirect { id }
        userErrors { field message }
      }
    }
    """
    variables = {
        "urlRedirect": {
            "path": path_from,
            "target": path_to
        }
    }
    
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
        return res.json()
    except Exception as e:
        return {"errors": str(e)}

def run_test():
    token = get_access_token()
    if not token:
        print("Impossibile ottenere il token. Verifica che l'app supporti il Client Credentials Grant.")
        return

    print("Autenticazione riuscita. Eseguo test sui 2 prodotti...")
    
    test_cases = [
        {"sku": "790000", "old": "/piscina-quadrata-in-legno-gre-city-225x225x65-cm-790000.html", "new": "/products/piscine-in-legno-quadrata-city-225-x-225-x-68-cm"},
        {"sku": "790207", "old": "/piscine-gre-montaggio-prezzi-fuoriterra-alta-dimensioni-rotonda-ovale-costo-prezzo-giardino-bassa/piscina-fuori-terra-in-legno-rettangolare-braga-790207-gre-sunbay-travi-metalliche-pino.html", "new": "/products/piscine-in-legno-rettangolare-marbella-2-420-x-270-x-117cm"}
    ]

    for item in test_cases:
        print(f"\n[SKU {item['sku']}] Creando redirect: {item['old']} -> {item['new']}")
        result = create_redirect(token, item['old'], item['new'])
        
        if result.get('data', {}).get('urlRedirectCreate', {}).get('urlRedirect'):
            print("  [OK] Successo!")
        else:
            errors = result.get('data', {}).get('urlRedirectCreate', {}).get('userErrors', [])
            print(f"  [ERRORE] {errors if errors else result.get('errors')}")
        time.sleep(0.5)

if __name__ == "__main__":
    run_test()
