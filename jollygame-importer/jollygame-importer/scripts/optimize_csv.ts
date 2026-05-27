import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";
import dotenv from "dotenv";
import Groq from "groq-sdk";

dotenv.config();

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

const CATEGORY_MAP: Record<string, string> = {
    "piscina": "Categoria:Piscine",
    "filtro": "Sottocategoria:Filtri",
    "pompa": "Sottocategoria:Pompe per piscine",
    "cloro": "Sottocategoria:Prodotti chimici",
    "pulitore": "Categoria:Pulitori",
    "robot": "Sottocategoria:Pulitori elettrico",
    "copertura": "Categoria:Coperture",
    "riscaldamento": "Categoria:Riscaldamento",
    "pompa di calore": "Sottocategoria:Pompe di calore",
    "doccia": "Sottocategoria:Docce",
    "liner": "Sottocategoria:Liner",
    "scaletta": "Sottocategoria:Scalette",
    "skimmer": "Sottocategoria:Skimmer",
    "faro": "Sottocategoria:Illuminazione",
    "luce": "Sottocategoria:Illuminazione",
    "sale": "Sottocategoria:Elettrolisi del sale",
    "ph": "Sottocategoria:Analisi dell'acqua"
};

async function optimizeTitle(oldTitle: string, vendor: string, retries = 3) {
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const prompt = `Riscrivi il titolo di questo prodotto per un e-commerce di piscine (Shopify).
Prodotto Originale: ${oldTitle}
Fornitore: ${vendor}

Regole:
1. Usa il formato "Titolo Prodotto [Modello/Serie] [Specifiche principali]"
2. Rendi il titolo elegante e professionale (Capitalize Each Word).
3. Rimuovi codici interni inutili ma tieni lo SKU se fa parte del nome comune.
4. Lunghezza ideale: 50-70 caratteri.
5. Rispondi SOLO con il nuovo titolo, niente commenti.`;

            const completion = await groq.chat.completions.create({
                messages: [{ role: "user", content: prompt }],
                model: "llama-3.1-8b-instant",
            });

            return completion.choices[0]?.message?.content?.trim().replace(/"/g, '') || oldTitle;
        } catch (e: any) {
            if (e?.status === 429 && attempt < retries) {
                const waitTime = 5000 * attempt;
                console.log(`  ⚠️ Rate limit hit. Waiting ${waitTime/1000}s before retry...`);
                await new Promise(r => setTimeout(r, waitTime));
                continue;
            }
            console.error(`  ❌ Errore Groq per ${oldTitle}:`, e.message || e);
            return oldTitle;
        }
    }
    return oldTitle;
}

function toCSV(data: any[]) {
    if (data.length === 0) return "";
    const headers = Object.keys(data[0]);
    const rows = data.map(row => 
        headers.map(header => {
            let val = row[header] || "";
            if (typeof val === "string") {
                val = val.replace(/"/g, '""');
                if (val.includes(",") || val.includes("\n") || val.includes('"')) {
                    val = `"${val}"`;
                }
            }
            return val;
        }).join(",")
    );
    return [headers.join(","), ...rows].join("\n");
}

async function processFile(inputFile: string, outputFile: string, vendor: string) {
    const inputPath = path.resolve(inputFile);
    if (!fs.existsSync(inputPath)) return;

    console.log(`Processing ${inputFile}...`);
    const fileContent = fs.readFileSync(inputPath, "utf-8");
    let records = parse(fileContent, { columns: true, skip_empty_lines: true });

    const outputRows = [];
    let i = 0;
    for (const record of records) {
        i++;
        if (i % 20 === 0) console.log(`  [${i}/${records.length}] Optimizing: ${record.Titolo}`);
        
        const oldTitle = record.Titolo;
        record.Titolo_Originale = oldTitle;
        record.Titolo = await optimizeTitle(oldTitle, vendor);

        // Taxonomy refinement
        const tags = (record.Tags || "").toLowerCase();
        const searchPool = (record.Titolo + " " + tags).toLowerCase();
        const newTags = [];
        
        for (const [key, val] of Object.entries(CATEGORY_MAP)) {
            if (searchPool.includes(key)) newTags.push(val);
        }
        
        newTags.push(`Brand:${vendor}`);
        if (tags.includes("ricambio")) newTags.push("Ricambio");
        
        // Ensure Categoria if missing
        if (!newTags.some(t => t.startsWith("Categoria:"))) {
            if (newTags.some(t => t.includes("Filtri") || t.includes("Pompe"))) newTags.push("Categoria:Filtraggio");
            else if (newTags.some(t => t.includes("Prodotti") || t.includes("Analisi"))) newTags.push("Categoria:Trattamento acqua");
            else if (newTags.some(t => t.includes("Piscine"))) newTags.push("Categoria:Piscine");
            else newTags.push("Categoria:Accessori");
        }
        
        record.Tags = Array.from(new Set(newTags)).join(",");
        outputRows.push(record);
        
        await new Promise(r => setTimeout(r, 400)); // Rate limit safety
    }

    const csvOutput = toCSV(outputRows);
    fs.writeFileSync(path.resolve(outputFile), csvOutput);
    console.log(`Saved to ${outputFile}`);
}

async function main() {
    await processFile("../../intex_pools_only.csv", "../../gold_intex_final.csv", "Intex");
    await processFile("../../bestway_pools_only.csv", "../../gold_bestway_final.csv", "Bestway");
    await processFile("../../fluidra_unique_import.csv", "../../gold_fluidra_final.csv", "Fluidra");
}

main().catch(console.error);
