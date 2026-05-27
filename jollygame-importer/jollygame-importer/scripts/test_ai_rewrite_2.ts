import dotenv from "dotenv";
import Groq from "groq-sdk";
import fs from "fs";

dotenv.config();

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function testRewrite2() {
    console.log("🤖 Avvio test riscrittura AI per Piscina Pacific...");

    const product = JSON.parse(fs.readFileSync("test_product_data_2.json", "utf-8"));
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
    - Deve essere esplicativo e includere: Brand + Modello + Forma. Non inserire dimensioni specifiche se il prodotto ha varianti.
    - Lunghezza ideale: 50-70 caratteri.
    - Esempio: "Piscina in Acciaio Gre Pacific Ovale - Kit Completo"

    REQUISITI DESCRIZIONE (in HTML pulito, usa solo <p>, <ul>, <li>, <strong>, <h3>):
    1. INTRODUZIONE: Un paragrafo che evochi il piacere e i vantaggi di questo prodotto. Deve essere universale e valere per qualsiasi variante dimensionale.
    2. CARATTERISTICHE (Lista puntata): Descrivi i materiali, la qualità costruttiva e i punti di forza. NON menzionare dimensioni esatte, pesi o volumi che potrebbero variare. Parla della linea di prodotto in generale.
    3. QUALITÀ E DURATA: Breve testo sulla resistenza nel tempo e l'affidabilità del brand.
    4. CONCLUSIONE: Invito all'acquisto su JollyGame.

    REGOLA FONDAMENTALE: 
    - NON menzionare MAI che esistono "varie dimensioni", "seleziona dal menu a tendina" o "diverse varianti".
    - La descrizione deve essere scritta come se fosse per un prodotto unico, concentrandosi sui pregi assoluti della serie/modello che rimangono identici a prescindere dalla misura acquistata.

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

    fs.writeFileSync("test_ai_output_2.json", JSON.stringify(result, null, 2));
    console.log("\n✅ Test completato! Risultato salvato in 'test_ai_output_2.json'");
    console.log("\n--- NUOVO TITOLO ---");
    console.log(result.title);
    console.log("\n--- NUOVA DESCRIZIONE ---");
    console.log(result.descriptionHtml);
}

testRewrite2().catch(console.error);
