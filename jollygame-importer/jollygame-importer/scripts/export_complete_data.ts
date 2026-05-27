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

async function exportEverything() {
  console.log("📥 Avvio Esportazione MASSIVA di tutti i campi...");

  let hasNextPage = true;
  let cursor = null;
  const allProducts: any[] = [];

  while (hasNextPage) {
    const query = `
    query getFull($cursor: String) {
      products(first: 50, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          handle
          status
          vendor
          productType
          tags
          descriptionHtml
          options { name }
          featuredMedia { preview { image { url } } }
          metafields(first: 50) {
            nodes { namespace key value }
          }
          variants(first: 100) {
            nodes {
              id
              sku
              barcode
              price
              compareAtPrice
              weight
              weightUnit
              inventoryQuantity
              inventoryPolicy
              inventoryManagement
              selectedOptions { name value }
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) {
        console.error("❌ Errore nel download:", res.errors);
        break;
    }

    allProducts.push(...res.data.products.nodes);
    console.log(`   📦 Scaricati ${allProducts.length} prodotti...`);

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  fs.writeFileSync("complete_data_dump.json", JSON.stringify(allProducts, null, 2));
  console.log("\n✅ DUMP COMPLETO SALVATO (complete_data_dump.json)");
}

exportEverything().catch(console.error);
