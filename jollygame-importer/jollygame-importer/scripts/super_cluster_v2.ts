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
Raggruppali in pochissime FAMIGLIE industriali (MASTER).
Esempi: "Piscina Power Steel Rettangolare", "Piscina Power Steel Rotonda", "Idromassaggio PureSpa".

Restituisci JSON:
{
  "mapping": [
    { "original": "Titolo X", "master": "Nome Famiglia Unificata", "variant": "Misura + Kit" }
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
            console.log(`  ⚠️ Retry ${attempt}/3...`);
            await new Promise(r => setTimeout(r, 5000));
        }
    }
    return [];
}

async function main() {
    const csvPath = path.resolve("../../gold_consolidated_final.csv");
    const content = fs.readFileSync(csvPath, "utf-8");
    const allRecords = parse(content, { columns: true, skip_empty_lines: true });

    // Filter only those that haven't been super-clustered yet (heuristic: Variant_Detail is still just a dimension or Standard)
    // Actually, let's just re-run on all Pools for consistency
    const pools = allRecords.filter((r: any) => r.Tags.toLowerCase().includes("piscine"));
    const others = allRecords.filter((r: any) => !r.Tags.toLowerCase().includes("piscine"));

    console.log(`🏊‍♂️ Recupero Super-Aggregazione con modello 8B per ${pools.length} piscine...`);

    const batchSize = 40; // Più grande per 8B
    for (let i = 0; i < pools.length; i += batchSize) {
        const batch = pools.slice(i, i + batchSize);
        console.log(`  [${i + batch.length}/${pools.length}] Processing...`);
        const mapping = await getMasterClustering(batch);
        
        batch.forEach(record => {
            const m = mapping.find((item: any) => item.original === record.Titolo);
            if (m) {
                record.Master_Title = m.master;
                record.Variant_Detail = m.variant;
            }
        });
        await new Promise(r => setTimeout(r, 800));
    }

    const headers = Object.keys(allRecords[0]);
    const rows = [...pools, ...others].map(r => headers.map(h => `"${String(r[h] || "").replace(/"/g, '""')}"`).join(","));
    fs.writeFileSync("../../gold_consolidated_final.csv", [headers.join(","), ...rows].join("\n"));
    
    console.log("✅ Super-Aggregazione FINALE completata!");
}

main().catch(console.error);
