
import shopify
import pandas as pd
import urllib.parse
import time
import os

# CREDENZIALI FORNITE
SHOP_URL = "jollygamepiscine.myshopify.com"
API_KEY = "3b1522894ce78d0f28f711abda547b3d"
API_SECRET = "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"
API_VERSION = "2026-04"
SCOPES = ['write_content', 'read_content']

def get_path(url):
    if not isinstance(url, str) or not url.startswith("http"):
        return None
    return urllib.parse.urlparse(url).path

def start_import(token):
    session = shopify.Session(SHOP_URL, API_VERSION, token)
    shopify.ShopifyResource.activate_session(session)
    
    csv_path = "C:/Users/Riccardo/Desktop/Manfredo/JollyGame/mapping_completo_PER_LAVORO_MANUALE.csv"
    if not os.path.exists(csv_path):
        print(f"Errore: File non trovato in {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"\nConnesso a {SHOP_URL}. Inizio creazione redirect...")
    
    count = 0
    for index, row in df.iterrows():
        old_url = row.get('Redirect_From_DA_INCOLLARE')
        new_url = row.get('Shopify_URL_Attuale')
        
        if pd.notna(old_url) and pd.notna(new_url) and "jollygame.it" in new_url:
            path_from = get_path(old_url)
            path_to = get_path(new_url)
            
            if path_from and path_to and path_from != path_to:
                try:
                    # Crea nuovo redirect
                    redirect = shopify.Redirect.create({
                        "path": path_from,
                        "target": path_to
                    })
                    if redirect.errors:
                        print(f"[{index+1}] Errore su {path_from}: {redirect.errors.full_messages()}")
                    else:
                        print(f"[{index+1}] Creato: {path_from} -> {path_to}")
                        count += 1
                except Exception as e:
                    print(f"[{index+1}] Eccezione: {e}")
                time.sleep(0.5)
    
    print(f"\nLavoro terminato! Creati {count} redirect.")

if __name__ == "__main__":
    shopify.Session.setup(api_key=API_KEY, secret=API_SECRET)

    # Provo a creare una sessione temporanea per l'autenticazione
    session = shopify.Session(SHOP_URL, API_VERSION)
    auth_url = session.create_permission_url(SCOPES, "https://localhost")

    print("="*60)
    print("CONFIGURAZIONE SESSIONE OAUTH 2026")
    print("="*60)
    print(f"1. Copia e incolla questo URL nel tuo browser:\n\n{auth_url}\n")
    print("2. Clicca su 'Installa App'.")
    print("3. Verrai rimandato a una pagina 'impossibile raggiungere il sito' (localhost).")
    print("4. Copia TUTTO l'URL della barra degli indirizzi o solo il valore dopo '?code='")
    print("="*60)

    code_input = input("\nIncolla qui l'URL o il codice: ").strip()

    if "code=" in code_input:
        code = code_input.split("code=")[1].split("&")[0]
    else:
        code = code_input

    try:
        print("\nScambio del codice con l'Access Token...")
        access_token = session.request_token({"code": code})
        print(f"Token ottenuto con successo!")
        start_import(access_token)
    except Exception as e:
        print(f"\nErrore durante lo scambio del token: {e}")
        print("Assicurati di aver usato il codice correttamente e che l'app abbia i permessi giusti.")
