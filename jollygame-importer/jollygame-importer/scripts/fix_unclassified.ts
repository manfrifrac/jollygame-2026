import dotenv from "dotenv";
import fs from "fs";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function fixUnclassifiedProducts() {
  console.log("🛠️  Sistemazione manuale degli ultimi prodotti non categorizzati...");

  const colQuery = `{ collections(first: 250) { nodes { id title } } }`;
  const colRes = await shopifyRequest(colQuery);
  const collections = colRes.data.collections.nodes;
  const colMap: Record<string, string> = {};
  collections.forEach((c: any) => { colMap[c.title.toLowerCase().trim()] = c.id; });

  const noPriceId = colMap["no price"];

  const query = `
    query {
      products(first: 250) {
        nodes {
          id
          title
          vendor
          collections(first: 5) { nodes { title } }
        }
      }
    }
  `;

  const res = await shopifyRequest(query);
  const products = res.data.products.nodes;
  let updatedCount = 0;

  for (const product of products) {
    const title = product.title.toLowerCase();
    const categories = product.collections.nodes.map((c: any) => c.title.toLowerCase());
    
    // Se è in 'no price' o non ha categorie significative
    if (categories.includes("no price") || categories.length === 0 || (categories.length === 1 && categories.includes("tutti i ricambi"))) {
        let targetColName = null;

        // Regole granulari
        if (title.includes("ra ") || title.includes("oa ") || title.includes("swy") || title.includes("robot") || title.includes("pulitore")) {
            targetColName = "pulitori elettrico";
        } else if (title.includes("z250") || title.includes("z350") || title.includes("z400") || title.includes("heat line") || title.includes("sirocco")) {
            targetColName = "pompe di calore";
        } else if (title.includes("ei2") || title.includes("exo") || title.includes("sale") || title.includes("eisalt")) {
            targetColName = "trattamento acqua";
        } else if (product.vendor === "Piscine Laghetto") {
            targetColName = "piscine fuori terra";
        } else if (product.vendor === "Gre" && (title.includes("piscina") || title.includes("ovale") || title.includes("rotonda"))) {
            targetColName = "piscine in legno";
        }

        const targetColId = targetColName ? colMap[targetColName] : null;

        if (targetColId) {
            console.log(`✨ Fix: ${product.title} -> [${targetColName}]`);
            const mutation = `
              mutation productUpdate($input: ProductInput!) {
                productUpdate(input: $input) {
                  product { id }
                  userErrors { message }
                }
              }
            `;
            const input: any = { id: product.id, collectionsToJoin: [targetColId] };
            if (noPriceId) input.collectionsToLeave = [noPriceId];

            await shopifyRequest(mutation, { input });
            updatedCount++;
            process.stdout.write(".");
            await new Promise(r => setTimeout(r, 200));
        }
    }
  }

  console.log(`\n\n✅ Fix finale completato! ${updatedCount} prodotti sistemati.`);
}

fixUnclassifiedProducts().catch(console.error);
