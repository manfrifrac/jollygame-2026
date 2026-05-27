# 🛠️ Guida Tecnica: Ecosistema di Scraping Massivo "Manfredo Stealth"

Questa guida descrive l'architettura e le tecniche avanzate utilizzate per lo scraping del catalogo **Fluidra PRO** (11.000+ record). Il sistema è progettato per essere resiliente, furtivo e capace di gestire relazioni complesse (Padre-Figlio).

---

## 🏗️ Architettura del Sistema

Il progetto è suddiviso in 6 fasi logiche, ognuna con script dedicati:

### Fase 1: Estrazione Tassonomia (`extract_fluidra_categories.py`)
*   **Scopo**: Mappare l'intero albero di navigazione del fornitore.
*   **Dinamica**: Scansiona il menu principale per raccogliere coppie `Etichetta: URL`.
*   **Output**: `fluidra_categories.json`.

### Fase 2: Crawling Link Prodotti (`collect_all_product_links_v4.py`)
*   **Tecnica**: Navigazione ricorsiva delle categorie con gestione della **paginazione** (Magento `.action.next`).
*   **Stealth**: Rilevamento errori 504/403 e rotazione automatica IP tramite **Mullvad VPN**.
*   **Deduplicazione**: Pulizia dei parametri URL (es. rimuove `?tab=...`) per identificare i prodotti base unici.
*   **Output**: `fluidra_product_links_map.json`.

### Fase 3: Ispezione Dinamica (`debug_single_product.py`)
*   **Reverse Engineering**: Analisi del caricamento asincrono (JavaScript/Knockout.js).
*   **EAN Visibility**: Scoperta critica -> L'EAN viene servito dal server solo se il browser è in modalità **Headless=False** (visibile). Se il browser è invisibile, il dato viene omesso per protezione anti-bot.

### Fase 4: Scraper Turbo Massivo (`mass_product_scraper.py`)
Il motore principale del progetto.
*   **Multi-Tab Concurrency**: Gestisce 3-5 schede (pagine) parallele nello stesso contesto browser per triplicare la velocità.
*   **VPN Sync**: Sincronizza la rotazione dell'IP ogni 20-30 prodotti. Chiude il browser, cambia IP con `rotate_vpn.py`, riapre e riprende.
*   **JS Injection**: Usa `page.evaluate()` per estrarre SKU e dati sensibili direttamente dalla memoria del browser, bypassando i limiti del DOM statico.

### Fase 5: Gestione Esplosi e Ricambi (`deep_product_scraper_v4.py`)
*   **Relazioni**: Identifica se un prodotto ha una tab "Esploso".
*   **Data Attributes**: Estrae i dati dai tag `.spare-container-fix-item` (data-sku, data-name, data-price, data-position).
*   **Mapping Grafico**: Salva l'URL dell'immagine dello schema (`diagram_url`) e lo collega a ogni ricambio tramite la sua posizione numerica (`diagram_index`).

### Fase 6: Archivio Media (`download_media.py`)
*   **Multi-threading**: Scarica simultaneamente 10 file per massimizzare la banda.
*   **Sanificazione**: Rinomina i file in `SKU_1.jpg` o `SKU_Manuale_IT.pdf` rimuovendo caratteri non validi per Windows.

---

## 🛡️ Strategie Stealth & Anti-Bot

Per evitare il ban dell'IP e del profilo utente, sono state implementate:
1.  **Playwright-Stealth**: Modifica le impronte digitali del browser (canvas, webgl, vendor) per simulare un browser umano.
2.  **Human Jitter**: 
    *   Attese casuali tra caricamento e azione (5-12 secondi).
    *   Scroll della pagina a velocità variabile.
    *   Movimenti del mouse non lineari.
3.  **Rotazione IP Mullvad**: Integrazione CLI con `mullvad disconnect` / `mullvad connect` in località casuali europee.
4.  **Persistent Context**: Uso di una cartella `playwright_user_data` per mantenere i cookie di sessione (login) ed evitare di rifare l'autenticazione ad ogni avvio.

---

## 📊 Schema Database (SQLite)

Il file `fluidra_catalog.db` utilizza due tabelle principali:

### Tabella `products`
| Campo | Tipo | Descrizione |
| :--- | :--- | :--- |
| `sku` | TEXT (PK) | Identificativo univoco (es. WR000500) |
| `ean` | TEXT | Codice a barre 13 cifre |
| `title` | TEXT | Titolo pulito (estratto dopo la pipe `|`) |
| `price_net` | REAL | Prezzo scontato per l'utente |
| `stock_italy`| INTEGER | Quantità disponibile nel magazzino Italia |
| `images_json`| TEXT | Lista URL immagini in formato JSON |
| `docs_json`  | TEXT | Lista PDF (Manuali/Depliant) in JSON |
| `diagram_url`| TEXT | URL dell'immagine dello schema ricambi |
| `is_spare`   | INTEGER | 1 se è un ricambio, 0 se prodotto principale |

### Tabella `product_relations`
Collega i prodotti ai loro ricambi:
*   `parent_sku`: SKU del prodotto principale.
*   `child_sku`: SKU del ricambio.
*   `diagram_index`: Numero di posizione nello schema grafico (es. "1", "2a").

---

## 🚀 Come applicarlo a un nuovo Fornitore

1.  **Analisi Iniziale**: Apri il sito in Incognito. Se vedi `/catalog/category/` o `data-mage-init`, è un sito **Magento**. Puoi riusare l'80% di questo codice.
2.  **Test Headless**: Verifica se l'EAN è visibile in modalità "invisibile". Se non lo è, imposta `headless=False` in Playwright.
3.  **Mappa i Selettori**: Usa `inspect_page.py` per trovare i selettori di Titolo, SKU e Prezzo.
4.  **Configura Mullvad**: Assicurati che `rotate_vpn.py` possa eseguire il comando `mullvad` sul tuo PC.
5.  **Lancio**: Esegui prima la raccolta link, poi lo scraper massivo.

---
*Documentazione generata per Manfredo Job Finder - 22 Aprile 2026*
