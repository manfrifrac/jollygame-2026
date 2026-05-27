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

async function forceFixLaghetto() {
  console.log("🛠️  Fix FORZATO Laghetto (Senza filtri vendor)...");

  const query = `
    query {
      products(first: 250) {
        nodes {
          id title vendor
        }
      }
    }
  `;
  const res = await shopifyRequest(query);
  const products = res.data.products.nodes;
  let updatedCount = 0;

  for (const product of products) {
    const title = product.title.toLowerCase();
    const isLaghetto = product.vendor === "Piscine Laghetto" || title.includes("ninfea") || title.includes("dolcevita") || title.includes("bluespring") || title.includes("playa");

    if (isLaghetto) {
        let shape = null;
        if (title.includes("city")) shape = "Quadrata";
        else if (title.includes("playa") || title.includes("dolcevita") || title.includes("bluespring") || title.includes("divina") || title.includes("classic")) shape = "Rettangolare";
        else if (title.includes("ninfea") || title.includes("pop")) shape = "Ovale";

        if (shape) {
            console.log(`✨ Shape [${shape}] -> ${product.title}`);
            const mutation = `
              mutation upd($input: ProductInput!) {
                productUpdate(input: $input) {
                  product { id }
                }
              }
            `;
            await shopifyRequest(mutation, {
              input: {
                id: product.id,
                metafields: [{ namespace: "custom", key: "forma", value: shape, type: "single_line_text_field" }]
              }
            });
            updatedCount++;
        }
    }
  }
  console.log(`✅ Concluso. Aggiornati ${updatedCount} modelli Laghetto.`);
}

forceFixLaghetto().catch(console.error);
