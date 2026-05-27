import dotenv from "dotenv";
import Groq from "groq-sdk";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function cleanTitleAI(oldTitle: string) {
  try {
    const prompt = `Sei un esperto di copywriting per e-commerce. Il seguente titolo prodotto Shopify è ridondante o scritto male (spesso ripete la categoria). 
    Riscrivilo in modo professionale, pulito e accattivante, rimuovendo le ripetizioni ma mantenendo il modello tecnico e il senso del prodotto.
    
    Esempi:
    - "Robots Robot pulitore elettrico" -> "Robot pulitore elettrico"
    - "Clorinatore salino Cloratore salino collegato" -> "Clorinatore salino collegato"
    - "Anthracite ovale" -> "Piscina Anthracite Ovale"
    
    Titolo originale: "${oldTitle}"
    
    Rispondi SOLO con il nuovo titolo, senza commenti.`;

    const completion = await groq.chat.completions.create({
      messages: [{ role: "user", content: prompt }],
      model: "llama-3.3-70b-versatile",
    });

    return completion.choices[0]?.message?.content?.replace(/"/g, '') || oldTitle;
  } catch (e) {
    return oldTitle;
  }
}

async function fixAllTitles() {
  console.log("🔍 Avvio Bonifica Titoli con AI...");

  const query = `{
    products(first: 250) {
      nodes {
        id
        title
        vendor
      }
    }
  }`;

  const res = await shopifyRequest(query);
  const products = res.data.products.nodes;

  for (const product of products) {
    const originalTitle = product.title;
    
    // Filtriamo: procediamo solo se il titolo sembra ridondante (es: parole ripetute o troppo corte)
    const words = originalTitle.toLowerCase().split(" ");
    const hasDuplicates = new Set(words).size !== words.length;
    
    // In questo caso, per sicurezza, chiediamo all'AI di valutare tutti i titoli caricati dai CSV
    console.log(`\n⚖️ Valutazione: ${originalTitle}`);
    const newTitle = await cleanTitleAI(originalTitle);

    if (newTitle !== originalTitle) {
      console.log(`  ✨ Nuovo Titolo: ${newTitle}`);
      
      const mutation = `
      mutation productUpdate($input: ProductInput!) {
        productUpdate(input: $input) {
          product { id title }
          userErrors { message }
        }
      }
      `;

      await shopifyRequest(mutation, {
        input: {
          id: product.id,
          title: newTitle,
          metafields: [{
            namespace: "global",
            key: "title_tag",
            type: "string",
            value: `${newTitle} | JollyGame`
          }]
        }
      });
    } else {
      console.log(`  ✅ Titolo già corretto.`);
    }

    await new Promise(r => setTimeout(r, 1000));
  }

  console.log("\n✅ Bonifica titoli completata!");
}

fixAllTitles().catch(console.error);
