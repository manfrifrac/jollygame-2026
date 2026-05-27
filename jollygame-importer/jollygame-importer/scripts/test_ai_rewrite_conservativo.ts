import dotenv from "dotenv";
import Groq from "groq-sdk";
import fs from "fs";

dotenv.config();

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function testRewriteConservativo() {
    console.log("🤖 Avvio test AI CONSERVATIVO per Piscina Pacific...");

    const product = JSON.parse(fs.readFileSync("test_product_data_2.json", "utf-8"));
    const techSpecs = product.metafields.nodes
        .filter((m: any) => m.namespace === "custom")
        .map((m: any) => `${m.key}: ${m.value}`)
        .join(", ");

    const prompt = `
    Sei un esperto copywriter SEO senior per JollyGame. Devi riscrivere TITOLO e DESCRIZIONE.
    
    OBIETTIVO: Creare una descrizione Premium senza PERDERE NESSUN DETTAGLIO TECNICO reale, ma rendendola corretta per tutte le varianti.

    TITOLO ATTUALE: ${product.title}
    DATI TECNICI: ${techSpecs}
    DESCRIZIONE ORIGINALE DA ANALIZZARE: ${product.descriptionHtml}

    COMPITI:
    1. ANALISI: Estrai dalla descrizione originale dettagli come materiali (acciaio galvanizzato), tipi di componenti (scala a forbice), tempi di montaggio, e garanzie.
    2. PRESERVAZIONE: Includi OBBLIGATORIAMENTE tutti questi dettagli nella nuova descrizione.
    3. UNIVERSALITÀ: Identifica i dati che cambiano tra le varianti (misure esatte, volume esatto in m3, portata esatta del filtro). Sostituiscili con diciture generali (es: "volume e dimensioni variabili in base alla configurazione scelta").
    4. TITOLO: Genera un titolo esplicativo (Brand + Modello + Forma).

    STRUTTURA HTML RICHIESTA:
    - <h3> per i titoli delle sezioni.
    - <p> per i testi.
    - <ul> e <li> per l'elenco del kit e specifiche.
    - <strong> per i termini chiave.

    RISPONDI ESCLUSIVAMENTE IN FORMATO JSON:
    {
      "title": "Titolo",
      "descriptionHtml": "HTML"
    }
    `;

    const chatCompletion = await groq.chat.completions.create({
        messages: [{ role: "user", content: prompt }],
        model: "llama-3.3-70b-versatile",
        response_format: { type: "json_object" }
    });

    const result = JSON.parse(chatCompletion.choices[0]?.message?.content || "{}");

    fs.writeFileSync("test_ai_output_conservativo.json", JSON.stringify(result, null, 2));
    console.log("\n✅ Test completato! Risultato salvato in 'test_ai_output_conservativo.json'");
    console.log("\n--- NUOVO TITOLO ---");
    console.log(result.title);
    console.log("\n--- NUOVA DESCRIZIONE (Check preservazione dati) ---");
    console.log(result.descriptionHtml);
}

testRewriteConservativo().catch(console.error);
