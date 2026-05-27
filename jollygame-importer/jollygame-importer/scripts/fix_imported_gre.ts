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

async function fixImportedProducts() {
  const newProducts = JSON.parse(fs.readFileSync("new_gre_products_to_import.json", "utf8"));
  console.log(`🛠️ Riparazione di ${newProducts.length} prodotti importati (SKU e Prezzi)...`);

  // 1. Get all products on Shopify with tag Listino:2026
  let hasNextPage = true;
  let cursor = null;
  const shopifyMap: Record<string, { pid: string, vid: string }> = {};

  while (hasNextPage) {
    const query = `
    query getNew($cursor: String) {
      products(first: 250, after: $cursor, query: "tag:'Listino:2026'") {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          variants(first: 1) { nodes { id } }
        }
      }
    }
    `;
    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;
    
    for (const p of res.data.products.nodes) {
        shopifyMap[p.title] = { pid: p.id, vid: p.variants.nodes[0].id };
    }
    
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`🔍 Trovati ${Object.keys(shopifyMap).length} prodotti da riparare su Shopify.`);

  let count = 0;
  for (const p of newProducts) {
      const data = shopifyMap[p.title];
      if (data) {
          const mutation = `
          mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
            productVariantsBulkUpdate(productId: $productId, variants: $variants) {
              product { id }
              userErrors { field message }
            }
          }
          `;
          
          const res = await shopifyRequest(mutation, {
              productId: data.pid,
              variants: [
                  {
                      id: data.vid,
                      price: p.price.toString(),
                      inventoryItem: {
                          sku: p.sku
                      },
                      inventoryPolicy: "CONTINUE"
                  }
              ]
          });

          if (res.data?.productVariantsBulkUpdate?.product) {
              count++;
              if (count % 20 === 0) console.log(`   ✅ Riparati ${count} prodotti...`);
          } else {
              console.error(`   ❌ Errore riparazione ${p.sku}:`, JSON.stringify(res.data?.productVariantsBulkUpdate?.userErrors || res.errors, null, 2));
          }
      }
  }

  console.log(`\n✅ Riparazione completata! ${count} prodotti ora hanno SKU e Prezzo corretti.`);
}

fixImportedProducts().catch(console.error);
