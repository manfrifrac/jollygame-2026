# Guida Tecnica: Costruzione App Importer Shopify 2026

Questa guida spiega come è stata costruita l'app `jollygame-importer` per gestire l'importazione massiva, l'upload binario delle immagini e l'ottimizzazione tramite Intelligenza Artificiale.

## 1. Scaffolding dell'App
L'app è basata sul template **Shopify Remix**, ma è stata estesa con utility CLI standalone in TypeScript.
*   **Inizializzazione:** `npx @shopify/cli@latest app init`
*   **Configurazione:** Il file `shopify.app.toml` definisce gli accessi richiesti (`write_products`, `write_metaobjects`, `write_publications`).

## 2. Il Flusso di Autenticazione (OAuth CLI)
Per le app CLI, non possiamo usare token statici limitati. Abbiamo implementato un server OAuth manuale (`scripts/generate_token.ts`):
1.  L'app avvia un server HTTP locale (porta 3000).
2.  Genera un URL di autorizzazione Shopify.
3.  L'utente autorizza l'app nel browser.
4.  Shopify rimanda un `code` al server locale.
5.  Il server scambia il `code` con un `access_token` permanente e lo salva nel file `.env`.

## 3. Upload Immagini Robusto (Staged Uploads)
Shopify 2026 richiede che i file vengano "pre-caricati" su storage cloud prima di essere associati a un prodotto.
*   **Fase A:** Chiamata GraphQL `stagedUploadsCreate` per ottenere credenziali S3/GCS.
*   **Fase B:** Upload binario (POST) del file fisico. **Regola d'oro:** il campo `file` deve essere l'ultimo nel form multipart.
*   **Fase C:** Associazione dell'URL risultante (`resourceUrl`) al prodotto tramite `productCreateMedia`.

## 4. Gestione Documentazione (Metaobjects)
Per caricare i PDF senza "sporcare" la descrizione:
1.  Si definisce un Metaobject `documento_tecnico`.
2.  Si caricano i PDF come voci di questo oggetto.
3.  Si collegano i prodotti tramite un metafield di tipo `list.metaobject_reference`.

## 5. Integrazione AI (Groq + Llama 3)
L'IA non è solo per la chat, qui è integrata nel workflow di importazione:
*   **Prompt Engineering:** Abbiamo istruito l'IA come esperto SEO per e-commerce.
*   **Elaborazione Batch:** Lo script `seo_optimizer.ts` cicla i prodotti, invia il contenuto grezzo a Groq e riceve HTML pulito e persuasivo da salvare su Shopify.

## 6. Logica di Pubblicazione Dinamica
Utilizzando la risorsa `publications`, l'app controlla il prezzo di ogni prodotto:
*   Se `price == 0`, lo script esegue `publishableUnpublish` specificamente per i canali Google e YouTube, mantenendo però il prodotto attivo per l'Online Store.

---

## 🛠️ Come modificare i prodotti in massa
Per aggiungere una nuova logica di modifica (es: cambiare i prezzi del 10%):
1.  Crea un nuovo file in `scripts/`.
2.  Usa la funzione `shopifyRequest` per interrogare i prodotti.
3.  Esegui una mutazione `productUpdate` per ogni ID trovato.
4.  Lancia lo script con `npx tsx scripts/tuo_script.ts`.
