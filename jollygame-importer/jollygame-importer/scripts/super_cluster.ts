import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";
import dotenv from "dotenv";
import Groq from "groq-sdk";

dotenv.config();
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function getMasterClustering(batch: any[]) {
    const titles = batch.map(r => r.Titolo);
    const prompt = `Analizza questo elenco di PISCINE e SPA. 
Raggruppale in pochissime FAMIGLIE industriali (MASTER).
Esempi di Famiglie: "Piscina Power Steel Rettangolare", "Piscina Power Steel Rotonda", "Piscina Prisma Frame Ovale", "Idromassaggio PureSpa", "Piscina Hydrium Acciaio".

Restituisci JSON:
{
  "mapping": [
    { "original": "Titolo X", "master": "Nome Famiglia Unificata", "variant": "Misura + Kit" }
  ]
}

IMPORTANTE: Sii molto aggressivo nell'unificare. Tutti i modelli "Power Steel" rettangolari devono finire sotto lo stesso Master, a prescindere dalle misure.

Titoli:
${titles.join("\n")}
`;

    try {
        const completion = await groq.chat.completions.create({
            messages: [{ role: "user", content: prompt }],
            model: "llama-3.3-70b-versatile",
            response_format: { type: "json_object" }
        });
        return JSON.parse(completion.choices[0].message.content || "{}").mapping;
    } catch (e) {
        console.error("Error:", e);
        return [];
    }
}

async function main() {
    const csvPath = path.resolve("../../gold_consolidated_final.csv");
    const content = fs.readFileSync(csvPath, "utf-8");
    const allRecords = parse(content, { columns: true, skip_empty_lines: true });

    // Isolate Pools/SPA
    const pools = allRecords.filter((r: any) => r.Tags.toLowerCase().includes("piscine"));
    const others = allRecords.filter((r: any) => !r.Tags.toLowerCase().includes("piscine"));

    console.log(`🏊‍♂️ Avvio Super-Aggregazione per ${pools.length} piscine...`);

    const batchSize = 20;
    for (let i = 0; i < pools.length; i += batchSize) {
        const batch = pools.slice(i, i + batchSize);
        console.log(`  Processing batch ${i/batchSize + 1}...`);
        const mapping = await getMasterClustering(batch);
        
        batch.forEach(record => {
            const m = mapping.find((item: any) => item.original === record.Titolo);
            if (m) {
                record.Master_Title = m.master;
                record.Variant_Detail = m.variant;
            }
        });
        await new Promise(r => setTimeout(r, 1500));
    }

    const finalRecords = [...pools, ...others];
    const headers = Object.keys(finalRecords[0]);
    const rows = finalRecords.map(r => headers.map(h => `"${String(r[h] || "").replace(/"/g, '""')}"`).join(","));
    fs.writeFileSync("../../gold_consolidated_final.csv", [headers.join(","), ...rows].join("\n"));
    
    console.log("✅ Super-Aggregazione completata!");
}

main().catch(console.error);
