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

async function rewriteDescription(currentHtml: string, title: string) {
  try {
    const prompt = `Sei un esperto SEO per e-commerce specializzato in piscine. Riscrivi la seguente descrizione prodotto per uno store Shopify.
    Prodotto: ${title}
    
    Obiettivi:
    1. Linguaggio persuasivo, elegante e professionale in italiano.
    2. Ottimizzazione SEO per parole chiave legate al brand Piscine Laghetto.
    3. Mantieni TUTTE le specifiche tecniche e i dettagli originali.
    4. Usa tag HTML puliti (h3, p, ul, li) per la struttura.
    5. Restituisci SOLO l'HTML della descrizione, senza introduzioni o commenti.

    Descrizione originale:
    ${currentHtml}`;

    const completion = await groq.chat.completions.create({
      messages: [{ role: "user", content: prompt }],
      model: "llama-3.3-70b-versatile",
    });

    return completion.choices[0]?.message?.content || currentHtml;
  } catch (e) {
    console.error(`  ❌ Errore Groq per ${title}:`, e);
    return currentHtml;
  }
}

async function optimizeSeo() {
  console.log("🔍 Avvio Ottimizzazione SEO e AI...");

  const query = `
  query($cursor: String) {
    products(first: 250, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        title
        vendor
        descriptionHtml
        metafields(first: 10) {
          nodes {
            namespace
            key
            value
          }
        }
      }
    }
  }
  `;

  let hasNext = true;
  let cursor = null;
  const products: any[] = [];

  while (hasNext) {
    const res = await shopifyRequest(query, { cursor });
    products.push(...res.data.products.nodes);
    hasNext = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  for (const product of products) {
    console.log(`\n⚙️ Elaborazione SEO: ${product.title}`);

    const updates: any = {};
    const metafieldsToUpdate = [];

    // 1. Riscrittura AI per Laghetto e Zodiac
    if (product.vendor === "Piscine Laghetto" || product.vendor === "Zodiac") {
      console.log(`  🤖 Riscrittura AI in corso per ${product.vendor}...`);
      const newDesc = await rewriteDescription(product.descriptionHtml, product.title);
      if (newDesc !== product.descriptionHtml) {
          updates.descriptionHtml = newDesc;
          console.log(`  ✨ Descrizione ottimizzata con AI.`);
      }
    }

    // 2. Controllo Meta Tags SEO
    const titleTag = product.metafields.nodes.find((m: any) => m.namespace === 'global' && m.key === 'title_tag');
    const descTag = product.metafields.nodes.find((m: any) => m.namespace === 'global' && m.key === 'description_tag');

    if (!titleTag) {
        const value = `${product.title} | JollyGame`.slice(0, 70);
        metafieldsToUpdate.push({ namespace: "global", key: "title_tag", type: "string", value });
        console.log(`  📝 Generato Title Tag.`);
    }

    if (!descTag) {
        // Pulisce l'HTML per creare lo snippet
        const cleanDesc = product.descriptionHtml.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
        const value = cleanDesc.slice(0, 155) + "...";
        metafieldsToUpdate.push({ namespace: "global", key: "description_tag", type: "string", value });
        console.log(`  📝 Generato Description Tag.`);
    }

    if (Object.keys(updates).length > 0 || metafieldsToUpdate.length > 0) {
        const mutation = `
        mutation productUpdate($input: ProductInput!) {
          productUpdate(input: $input) {
            product { id }
            userErrors { message }
          }
        }
        `;
        
        await shopifyRequest(mutation, {
          input: {
            id: product.id,
            ...updates,
            metafields: metafieldsToUpdate
          }
        });
    }
    
    // Delay per evitare rate limits (Groq e Shopify)
    await new Promise(r => setTimeout(r, 1500));
  }

  console.log("\n✅ Ottimizzazione SEO e AI completata!");
}

optimizeSeo().catch(console.error);
