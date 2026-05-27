import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";
import dotenv from "dotenv";
import Groq from "groq-sdk";

dotenv.config();
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function getGlobalClustering(batch: any[]) {
    const titles = batch.map(r => r.Titolo);
    const prompt = `Analizza questo elenco di prodotti per piscine e tempo libero. 
Raggruppali in FAMIGLIE industriali (MASTER) estremamente sintetiche.

Regole di Unificazione:
1. Tutti i teli di misure diverse -> "Telo di Copertura [Marca]"
2. Tutte le cartucce filtro -> "Cartuccia Filtro [Marca]"
3. Tutti i materassi della stessa serie -> "Materasso Gonfiabile [Serie]"
4. Tutte le pompe della stessa serie -> "Pompa Filtro [Serie]"
5. Tutte le scalette -> "Scaletta di Sicurezza per Piscine"

Restituisci JSON:
{
  "mapping": [
    { "original": "Titolo X", "master": "Nome Famiglia Unificata", "variant": "Dettaglio Specifico (Misura/Potenza/Kit)" }
  ]
}

Titoli:
${titles.join("\n")}
`;

    for (let attempt = 1; attempt <= 3; attempt++) {
        try {
            const completion = await groq.chat.completions.create({
                messages: [{ role: "user", content: prompt }],
                model: "llama-3.1-8b-instant",
                response_format: { type: "json_object" }
            });
            return JSON.parse(completion.choices[0].message.content || "{}").mapping;
        } catch (e: any) {
            console.log(`  ⚠️ Retry ${attempt}/3... (Error: ${e.message})`);
            await new Promise(r => setTimeout(r, 6000));
        }
    }
    return [];
}

async function main() {
    const csvPath = path.resolve("../../gold_consolidated_final.csv");
    const content = fs.readFileSync(csvPath, "utf-8");
    const allRecords = parse(content, { columns: true, skip_empty_lines: true });

    console.log(`🚀 Avvio Super-Aggregazione GLOBALE (Modello Veloce) per tutti i ${allRecords.length} prodotti...`);

    const batchSize = 35; 
    for (let i = 0; i < allRecords.length; i += batchSize) {
        const batch = allRecords.slice(i, i + batchSize);
        console.log(`  [${Math.min(i + batchSize, allRecords.length)}/${allRecords.length}] Processing batch...`);
        const mapping = await getGlobalClustering(batch);
        
        batch.forEach(record => {
            const m = mapping.find((item: any) => item.original === record.Titolo);
            if (m) {
                record.Master_Title = m.master;
                record.Variant_Detail = m.variant;
            }
        });
        await new Promise(r => setTimeout(r, 1200));
    }

    const headers = Object.keys(allRecords[0]);
    const rows = allRecords.map(r => headers.map(h => `"${String(r[h] || "").replace(/"/g, '""')}"`).join(","));
    fs.writeFileSync("../../gold_consolidated_final.csv", [headers.join(","), ...rows].join("\n"));
    
    console.log("✅ Super-Aggregazione GLOBALE completata!");
}

main().catch(console.error);
