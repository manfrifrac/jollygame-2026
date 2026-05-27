import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";
import dotenv from "dotenv";
import Groq from "groq-sdk";

dotenv.config();
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function getMasterTitles(titles: string[]) {
    const prompt = `Analizza questo elenco di prodotti per piscine. 
Raggruppali in "Modelli Master" (famiglie di prodotto).
Per ogni prodotto, restituisci:
1. "master": Nome pulito della famiglia (es: "Piscina Power Steel Rettangolare").
2. "variant": Dettaglio specifico (es: dimensione "412x201x122" o kit "Con Pompa").

Restituisci un JSON con questa struttura:
{
  "mapping": [
    { "original": "Titolo Originale Esatto", "master": "Titolo Master", "variant": "Dettaglio Variante" }
  ]
}

IMPORTANTE: "original" deve corrispondere esattamente a uno dei titoli forniti.

Titoli da elaborare:
${titles.join("\n")}
`;

    try {
        const completion = await groq.chat.completions.create({
            messages: [{ role: "user", content: prompt }],
            model: "llama-3.3-70b-versatile",
            response_format: { type: "json_object" }
        });
        const content = completion.choices[0].message.content || "{}";
        return JSON.parse(content).mapping;
    } catch (e) {
        console.error("  ❌ Errore batch:", e);
        return [];
    }
}

async function main() {
    const files = ["../../gold_intex_final.csv", "../../gold_bestway_final.csv", "../../gold_fluidra_final.csv"];
    let allRecords: any[] = [];
    
    for (const f of files) {
        const p = path.resolve(f);
        if (fs.existsSync(p)) {
            const content = fs.readFileSync(p, "utf-8");
            const records = parse(content, { columns: true, skip_empty_lines: true });
            allRecords = allRecords.concat(records);
        }
    }

    console.log(`🚀 Avvio consolidamento IA di ${allRecords.length} prodotti...`);
    
    const batchSize = 15; // Più piccolo per precisione 70b
    for (let i = 0; i < allRecords.length; i += batchSize) {
        const batch = allRecords.slice(i, i + batchSize);
        const titles = batch.map(r => r.Titolo);
        console.log(`  [${i + batch.length}/${allRecords.length}] Processing...`);
        
        const mapping = await getMasterTitles(titles);
        
        batch.forEach(record => {
            const m = mapping.find((item: any) => item.original === record.Titolo);
            if (m) {
                record.Master_Title = m.master;
                record.Variant_Detail = m.variant;
            } else {
                record.Master_Title = record.Titolo;
                record.Variant_Detail = "Standard";
            }
        });
        
        await new Promise(r => setTimeout(r, 1500)); // Rate limit safety
    }

    // Manual CSV generation (safe for quotes/commas)
    const headers = Object.keys(allRecords[0]);
    const rows = allRecords.map(r => headers.map(h => {
        let v = r[h] || "";
        return `"${String(v).replace(/"/g, '""')}"`;
    }).join(","));
    
    const csvContent = [headers.join(","), ...rows].join("\n");
    fs.writeFileSync("../../gold_consolidated_final.csv", csvContent);
    
    console.log("\n✅ Consolidamento completato!");
    console.log("📁 File salvato: gold_consolidated_final.csv");
}

main().catch(console.error);
