import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";

interface DocLink {
    title: string;
    url: string;
}

interface ProductDocs {
    productTitle: string;
    handle: string;
    docs: DocLink[];
}

function extractDocs() {
    console.log("📂 Inizio estrazione link PDF dai file locali...");
    
    const results: ProductDocs[] = [];

    // 1. Analisi Laghetto
    const laghettoPath = path.resolve("../../laghetto_full_export_enriched.csv");
    if (fs.existsSync(laghettoPath)) {
        console.log("📄 Leggo Laghetto CSV...");
        const records = parse(fs.readFileSync(laghettoPath, "utf-8"), { columns: true });
        for (const r of records) {
            const pdfString = r.PDF_Documenti || "";
            const links = pdfString.split(";").filter((s: string) => s.includes("|")).map((s: string) => {
                const [title, url] = s.split("|");
                return { title: title.trim(), url: url.trim() };
            });
            if (links.length > 0) {
                results.push({
                    productTitle: r.Titolo,
                    handle: (r.Titolo || "").toLowerCase().replace(/[^\w\s-]/g, '').replace(/[\s-]+/g, '-'),
                    docs: links
                });
            }
        }
    }

    // 2. Analisi Zodiac
    const zodiacPath = path.resolve("../../zodiac_enriched_data.csv");
    if (fs.existsSync(zodiacPath)) {
        console.log("📄 Leggo Zodiac CSV...");
        const content = fs.readFileSync(zodiacPath, "utf-8");
        const records = parse(content, { columns: true });
        for (const r of records) {
            const allText = JSON.stringify(r);
            const pdfMatches = allText.matchAll(/([^"<>|;\{\}]+)\|?(https?:\/\/[^"<>|;\{\} ]+\.pdf)/g);
            const links = Array.from(pdfMatches).map(m => ({
                title: m[1].trim().replace(/^"/, '').replace(/\\n/g, ' '),
                url: m[2].trim()
            })).filter(l => l.title.length > 2 && l.title.length < 100);

            if (links.length > 0) {
                results.push({
                    productTitle: r.Titolo,
                    handle: (r.Titolo || "").toLowerCase().replace(/[^\w\s-]/g, '').replace(/[\s-]+/g, '-'),
                    docs: links
                });
            }
        }
    }

    // 3. Analisi Fluidra (Export Shopify)
    const fluidraPath = path.resolve("../../fluidra_export_shopify.csv");
    if (fs.existsSync(fluidraPath)) {
        console.log("📄 Leggo Fluidra CSV...");
        const records = parse(fs.readFileSync(fluidraPath, "utf-8"), { columns: true });
        for (const r of records) {
            const allText = JSON.stringify(r);
            // Cerchiamo link PDF ovunque, ma con un'etichetta plausibile
            const pdfMatches = allText.matchAll(/(https?:\/\/[^"<>|; ]+\.pdf)/g);
            const rawUrls = Array.from(new Set(Array.from(pdfMatches).map(m => m[1])));
            
            const links = rawUrls.map(url => {
                let label = "Documento Tecnico";
                if (url.toLowerCase().includes("manual")) label = "Manuale di Installazione";
                if (url.toLowerCase().includes("leaflet") || url.toLowerCase().includes("depliant")) label = "Brochure Informativa";
                if (url.toLowerCase().includes("spare") || url.toLowerCase().includes("ricambio")) label = "Esploso Ricambi";
                return { title: label, url: url.trim() };
            });

            if (links.length > 0) {
                results.push({
                    productTitle: r.Title || r.Titolo,
                    handle: r.Handle,
                    docs: links
                });
            }
        }
    }

    fs.writeFileSync("extracted_documents_map.json", JSON.stringify(results, null, 2));
    console.log(`✅ Estrazione completata! Trovati documenti per ${results.length} prodotti.`);
}

extractDocs();
