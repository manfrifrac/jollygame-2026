# 🎯 JollyGame: Sistema Automazione Redirect Shopify 2026

Questo progetto gestisce la migrazione dei vecchi link di prodotto (da Grepool/Netrivals) verso il nuovo store Shopify di JollyGame, utilizzando le API GraphQL 2026.

---

## 🔑 Credenziali Shopify (Aggiornate 18 Aprile 2026)

*   **Store URL:** `jollygamepiscine.myshopify.com`
*   **API Version:** `2024-10`
*   **App Principale:** `jollygame-importer`
*   **Client ID:** `d616f7dc87082f688892cc90094362c1`
*   **API Secret:** `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`
*   **Scopes:** `write_products`, `write_content`, `write_metaobjects`, `write_publications`.

---

# 🚀 JollyGame Importer: Sistema Importazione & AI 2026

Situato in `jollygame-importer/jollygame-importer`, questo modulo è il cuore operativo per il caricamento del catalogo e l'ottimizzazione SEO.

## 🛠️ Architettura e Tecnologie

### 1. Sistema di Autenticazione (OAuth CLI)
Per superare i limiti dei token statici, l'app utilizza un server locale temporaneo per gestire il flusso OAuth.
*   **Script:** `scripts/generate_token.ts`
*   **Funzionamento:** Avvia un server su porta 3000, apre il browser dell'utente e cattura l'Access Token permanente dopo l'installazione.

### 2. Caricamento Immagini (Staged Uploads)
Per evitare blocchi di hotlinking, le immagini non vengono caricate via URL ma tramite upload binario diretto.
*   **Flusso:** `stagedUploadsCreate` -> `POST` binario (multipart/form-data) -> `productCreateMedia`.
*   **Precisione:** Le immagini sono caricate dai file locali presenti in `zodiac_images/` e `laghetto_images/`.

### 3. Gestione Documentazione (Metaobjects)
I manuali PDF vengono gestiti come entità indipendenti per massimizzare la pulizia e il SEO.
*   **Metaobject:** `documento_tecnico` (Campi: Titolo, URL File).
*   **Mapping:** Collegati ai prodotti tramite il metafield `custom.documentazione_tecnica`.

### 4. Ottimizzazione AI e SEO (Groq + Llama 3)
Il sistema utilizza l'IA per riscrivere contenuti e pulire i dati.
*   **Riscrittura Descrizioni:** Le schede **Piscine Laghetto** sono state interamente riscritte da un'IA istruita come esperto SEO.
*   **Bonifica Titoli:** Eliminazione automatica di ridondanze (es: "Robot Robot...") tramite Groq.
*   **Meta Tags:** Generazione automatica di Title Tag e Description Tag per tutti i 218 prodotti.

---

## 💻 Guida ai Comandi (CLI)

Eseguire questi comandi all'interno della cartella `jollygame-importer/jollygame-importer`:

| Comando | Descrizione |
| :--- | :--- |
| `npm run auth` | Avvia il login e rigenera l'Access Token nel file `.env`. |
| `npm run definitive-import` | Carica i prodotti dai CSV Zodiac/Laghetto (deduplicazione inclusa). |
| `npm run fix-images` | Carica le immagini locali per i prodotti che ne sono sprovvisti. |
| `npm run finalize-channels` | Gestisce la visibilità (rimuove da Google/YT i prodotti con prezzo 0). |
| `npm run seo-optimize` | Riscrive descrizioni Laghetto e genera Meta Tag per tutti. |
| `npx tsx scripts/activate_all.ts` | Attiva globalmente tutti i prodotti in stato Bozza. |
| `npx tsx scripts/extreme_deduplicate.ts` | Pulisce pixel-per-pixel le immagini doppie nelle gallery. |

---

# 🏊‍♂️ Moduli Scraping Originali

### 1. Zodiac Poolcare (`zodiac_deep_scraper.py`)
Estrae catalogo Zodiac Italia (80 prodotti) con navigazione ricorsiva.
*   **Immagini:** Recuperate ad alta risoluzione (Original).
*   **YouTube:** Cattura embed video dimostrativi.

### 2. Piscine Laghetto (`laghetto_deep_scraper.py`)
Estrae catalogo Laghetto (17 prodotti) inclusi PDF tecnici e schede materiali.

---

## 📂 File Risultanti Chiave
*   `zodiac_enriched_data.csv`: Database Zodiac pronto.
*   `laghetto_full_export_enriched.csv`: Database Laghetto arricchito.
*   `audit_results_v2.json`: Report prezzi trovati online durante l'audit.
