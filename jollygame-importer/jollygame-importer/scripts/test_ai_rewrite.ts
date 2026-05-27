import dotenv from "dotenv";
import Groq from "groq-sdk";
import fs from "fs";

dotenv.config();

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function testRewrite() {
    console.log("🤖 Avvio test riscrittura AI per RA 6300 iQ...");

    const product = JSON.parse(fs.readFileSync("test_product_data.json", "utf-8"));
    const techSpecs = product.metafields.nodes
        .filter((m: any) => m.namespace === "custom")
        .map((m: any) => `${m.key}: ${m.value}`)
        .join(", ");

    const prompt = `
    Sei un esperto copywriter SEO specializzato in prodotti per piscine di lusso per il brand JollyGame.
    Il tuo obiettivo è riscrivere il TITOLO e la DESCRIZIONE del prodotto seguente.

    TITOLO ATTUALE: ${product.title}
    BRAND: ${product.vendor}
    DATI TECNICI (Tassonomia): ${techSpecs}
    DESCRIZIONE ATTUALE: ${product.descriptionHtml}

    REQUISITI TITOLO:
    - Deve essere esplicativo e includere: Brand + Modello + Caratteristica Chiave/Dimensione.
    - Lunghezza ideale: 50-70 caratteri.
    - Esempio: "Robot Pulitore Zodiac Alpha RA 6300 iQ - Pulizia Intelligente App"

    REQUISITI DESCRIZIONE (in HTML pulito, usa solo <p>, <ul>, <li>, <strong>, <h3>):
    1. INTRODUZIONE: Un paragrafo emozionale.
    2. PUNTI DI FORZA (Lista puntata): 3-4 caratteristiche tecniche chiave.
    3. ESPERIENZA D'USO: Breve testo sull'uso quotidiano.
    4. CONCLUSIONE: Invito all'acquisto su JollyGame.

    RISPONDI ESCLUSIVAMENTE IN FORMATO JSON:
    {
      "title": "Nuovo Titolo Ottimizzato",
      "descriptionHtml": "Corpo della descrizione in HTML"
    }
    `;

    const chatCompletion = await groq.chat.completions.create({
        messages: [{ role: "user", content: prompt }],
        model: "llama-3.3-70b-versatile",
        response_format: { type: "json_object" }
    });

    const result = JSON.parse(chatCompletion.choices[0]?.message?.content || "{}");

    fs.writeFileSync("test_ai_output.json", JSON.stringify(result, null, 2));
    console.log("\n✅ Test completato! Risultato salvato in 'test_ai_output.json'");
    console.log("\n--- NUOVO TITOLO ---");
    console.log(result.title);
    console.log("\n--- NUOVA DESCRIZIONE ---");
    console.log(result.descriptionHtml);
}

testRewrite().catch(console.error);
