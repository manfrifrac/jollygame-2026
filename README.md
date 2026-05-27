# JollyGame 2026 - Sistema Automation & Ristrutturazione Catalogo

Sistema avanzato per la gestione, lo scraping e la sincronizzazione del catalogo prodotti per lo store Shopify di JollyGame.

## 🚀 Funzionalità Principali

### 1. Ristrutturazione Catalogo Gre 2026
- **Analisi Granulare:** Trasformazione di un listino Excel "piatto" in una struttura e-commerce a varianti multiple (Misura, Spessore, Kit).
- **Deduplicazione:** Pulizia automatica di SKU ed EAN duplicati nel database Shopify.
- **Sincronizzazione Prezzi:** Aggiornamento automatico basato sul listino 2026 con ricarichi personalizzati.

### 2. Sistema di Scraper Intelligenti
- **Official Scraper:** Bypass delle protezioni Incapsula/Imperva tramite Playwright e Stealth.
- **Multi-Source:** Recupero immagini da Grepool, Fluidra DAM, e rivenditori autorizzati.
- **Safe-Search:** Whitelist di domini affidabili per garantire la qualità dei contenuti.

### 3. Strumenti di Revisione
- **Image Reviewer Web App:** Applicazione web (Deployata su Vercel) per la validazione visuale delle immagini da parte dell'utente.

## 🛠️ Requisiti Tecnici
- Python 3.10+
- Node.js & NPM
- Playwright (per gli scraper)

## 📂 Struttura del Progetto
- `jollygame-importer/`: Core dell'applicazione di importazione Shopify.
- `jollygame-app/`: Scanner e applicazioni di supporto.
- `scripts/`: Script di utility per pulizia e analisi dati.
- `DESCRIZIONE_STRUTTURA_GRE.md`: Documentazione tecnica della gerarchia prodotti.

---
*Progetto sviluppato per Manfredo / JollyGame - 2026*
