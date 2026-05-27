
import pandas as pd
import requests
import urllib.parse
import time

# CONFIGURAZIONE SHOPIFY 2026
SHOP_URL = "jollygamepiscine.myshopify.com"
# SOSTITUISCI QUESTO TOKEN CON QUELLO NUOVO (shpat_...)
ACCESS_TOKEN = "shptka_56c35907b97a4928db981b5c8f926324" 
API_VERSION = "2026-04"
GRAPHQL_URL = f"https://{SHOP_URL}/admin/api/{API_VERSION}/graphql.json"

def get_path(url):
    """Estrae solo il path da un URL"""
    if not isinstance(url, str) or not url.startswith("http"):
        return None
    path = urllib.parse.urlparse(url).path
    return path

def create_redirect_graphql(path_from, path_to):
    query = """
    mutation urlRedirectCreate($urlRedirect: UrlRedirectInput!) {
      urlRedirectCreate(urlRedirect: $urlRedirect) {
        urlRedirect {
          id
          path
          target
        }
        userErrors {
          field
          message
        }
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
        "X-Shopify-Access-Token": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    response = requests.post(GRAPHQL_URL, json={"query": query, "variables": variables}, headers=headers)
    return response.json()

def process_csv():
    csv_path = "C:/Users/Riccardo/Desktop/Manfredo/JollyGame/mapping_completo_PER_LAVORO_MANUALE.csv"
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Errore caricamento CSV: {e}")
        return

    print(f"Inizio caricamento redirect su {SHOP_URL}...")
    
    count = 0
    for index, row in df.iterrows():
        old_url = row.get('Redirect_From_DA_INCOLLARE')
        new_url = row.get('Shopify_URL_Attuale')
        
        if pd.notna(old_url) and pd.notna(new_url) and "jollygame.it" in new_url:
            path_from = get_path(old_url)
            path_to = get_path(new_url)
            
            if path_from and path_to and path_from != path_to:
                print(f"[{index+1}] Creando: {path_from} -> {path_to}")
                result = create_redirect_graphql(path_from, path_to)
                
                if 'errors' in result:
                    print(f"  [ERRORE API] {result['errors']}")
                elif result.get('data', {}).get('urlRedirectCreate', {}).get('userErrors'):
                    errors = result['data']['urlRedirectCreate']['userErrors']
                    print(f"  [ERRORE UTENTE] {errors}")
                else:
                    print(f"  [OK] Successo.")
                    count += 1
                
                # Pausa per i limiti di rate (GraphQL ha un sistema a punti, 0.5s è prudente)
                time.sleep(0.5)

    print(f"\nFinito! Creati {count} redirect.")

if __name__ == "__main__":
    process_csv()
