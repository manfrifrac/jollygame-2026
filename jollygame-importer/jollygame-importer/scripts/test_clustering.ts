import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";
import dotenv from "dotenv";
import Groq from "groq-sdk";

dotenv.config();

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function clusterTest() {
    const csvPath = path.resolve("../../gold_intex_final.csv");
    const content = fs.readFileSync(csvPath, "utf-8");
    const records = parse(content, { columns: true, skip_empty_lines: true }).slice(0, 30);

    const titles = records.map((r: any) => r.Titolo);

    const prompt = `Analizza questo elenco di titoli di prodotti (Piscine Intex). 
Raggruppali in "Modelli Master" unificati.
Ogni Modello Master deve avere un titolo pulito e professionale (es: "Piscina Rettangolare Ultra XTR Frame").
Associa a ogni Modello Master i titoli originali che ne fanno parte come varianti.

Output atteso in JSON:
{
  "clusters": [
    {
      "master_title": "Titolo Pulito 1",
      "variants": ["Titolo Originale A", "Titolo Originale B"]
    }
  ]
}

Elenco Titoli:
${titles.join("\n")}
`;

    console.log("🧠 L'IA sta analizzando i cluster per 30 prodotti Intex...");
    const completion = await groq.chat.completions.create({
        messages: [{ role: "user", content: prompt }],
        model: "llama-3.1-8b-instant",
        response_format: { type: "json_object" }
    });

    const result = JSON.parse(completion.choices[0].message.content || "{}");
    console.log("\n--- RISULTATO CLUSTERING TEST ---");
    result.clusters.forEach((c: any) => {
        console.log(`\n📦 MASTER: ${c.master_title}`);
        c.variants.forEach((v: string) => console.log(`  - ${v}`));
    });
}

clusterTest().catch(console.error);
