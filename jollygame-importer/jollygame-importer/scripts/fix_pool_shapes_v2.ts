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

async function fixPoolShapesV2() {
  console.log("🛠️  Avvio fix metafield 'forma' per le piscine (V2)...");

  let hasNextPage = true;
  let cursor = null;
  let updatedCount = 0;

  while (hasNextPage) {
    const query = `
      query getPools($cursor: String) {
        products(first: 250, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id
            title
            vendor
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

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
      const title = product.title.toLowerCase();
      const vendor = product.vendor;
      
      // Identifichiamo se è una piscina (Zodiac robot esclusi)
      const isPool = (title.includes("piscina") || title.includes("ovale") || title.includes("rotonda") || title.includes("rettangolare")) &&
                     !title.includes("robot") && !title.includes("pulitore") && !title.includes("aspirapolvere") &&
                     (vendor === "Gre" || vendor === "Piscine Laghetto");

      if (isPool) {
        const currentShapeMeta = product.metafields.nodes.find((m: any) => m.key === "forma");
        const currentShape = currentShapeMeta ? currentShapeMeta.value : null;

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
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`\n\n✅ Fix completato! Aggiornate ${updatedCount} piscine.`);
}

fixPoolShapesV2().catch(console.error);
