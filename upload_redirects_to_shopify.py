
import pandas as pd
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
    """Estrae solo il path da un URL (es. /products/piscina-...)"""
    if not isinstance(url, str) or not url.startswith("http"):
        return None
    path = urllib.parse.urlparse(url).path
    return path

def create_redirects():
    csv_path = "C:/Users/Riccardo/Desktop/Manfredo/JollyGame/mapping_completo_PER_LAVORO_MANUALE.csv"
    df = pd.read_csv(csv_path)
    
    print(f"Caricamento redirect da {csv_path}...")
    
    count = 0
    for index, row in df.iterrows():
        old_url = row.get('Redirect_From_DA_INCOLLARE')
        new_url = row.get('Shopify_URL_Attuale')
        
        # Procedi solo se abbiamo entrambi i link e il target non è "Non trovato"
        if pd.notna(old_url) and pd.notna(new_url) and "jollygame.it" in new_url:
            path_from = get_path(old_url)
            path_to = get_path(new_url)
            
            if path_from and path_to and path_from != path_to:
                try:
                    print(f"[{index+1}] Creando redirect: {path_from} -> {path_to}")
                    
                    # Crea il redirect su Shopify
                    new_redirect = shopify.Redirect.create({
                        "path": path_from,
                        "target": path_to
                    })
                    
                    if new_redirect.errors:
                        print(f"  [ERRORE] {new_redirect.errors.full_messages()}")
                    else:
                        print(f"  [OK] Creato con successo.")
                        count += 1
                        
                except Exception as e:
                    print(f"  [ERRORE] Eccezione: {e}")
                
                # Pausa per evitare i limiti di velocità delle API (4 req/sec)
                time.sleep(0.5)

    print(f"\nOperazione completata! {count} redirect creati.")

if __name__ == "__main__":
    create_redirects()
