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

async function fixPoolShapes() {
  console.log("🛠️  Avvio fix metafield 'forma' per le piscine...");

  const query = `
    query {
      products(first: 250, query: "product_type:Piscina OR title:Piscina") {
        nodes {
          id
          title
          metafields(first: 20) {
            nodes {
              key
              value
            }
          }
        }
      }
    }
  `;

  const res = await shopifyRequest(query);
  const products = res.data.products.nodes;
  let updatedCount = 0;

  for (const product of products) {
    const title = product.title.toLowerCase();
    const currentShape = product.metafields.nodes.find((m: any) => m.key === "forma")?.value;

    if (!currentShape || currentShape === "Non definito") {
      let detectedShape = null;
      if (title.includes("ovale")) detectedShape = "Ovale";
      else if (title.includes("rotonda") || title.includes("tonda")) detectedShape = "Rotonda";
      else if (title.includes("rettangolare")) detectedShape = "Rettangolare";
      else if (title.includes("quadrata")) detectedShape = "Quadrata";
      else if (title.includes("otto")) detectedShape = "Forma di otto";

      if (detectedShape) {
        console.log(`✨ Rilevata forma [${detectedShape}] per: ${product.title}`);
        
        const mutation = `
          mutation productUpdate($input: ProductInput!) {
            productUpdate(input: $input) {
              product { id }
              userErrors { field message }
            }
          }
        `;

        await shopifyRequest(mutation, {
          input: {
            id: product.id,
            metafields: [
              {
                namespace: "custom",
                key: "forma",
                value: detectedShape,
                type: "single_line_text_field"
              }
            ]
          }
        });
        updatedCount++;
        process.stdout.write(".");
      }
    }
  }

  console.log(`\n\n✅ Fix completato! Aggiornate ${updatedCount} piscine.`);
}

fixPoolShapes().catch(console.error);
