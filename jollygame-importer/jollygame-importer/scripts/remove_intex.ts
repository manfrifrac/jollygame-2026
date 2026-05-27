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

async function removeIntexProducts() {
  console.log("🔍 Ricerca prodotti Intex da eliminare...");

  let hasNextPage = true;
  let cursor = null;
  const toDelete: string[] = [];

  while (hasNextPage) {
    const query = `
    query getIntex($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          vendor
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
        const titleMatch = product.title.toLowerCase().includes("intex");
        const vendorMatch = product.vendor.toLowerCase() === "intex";
        
        if (titleMatch || vendorMatch) {
            toDelete.push(product.id);
            console.log(`🚩 Trovato: ${product.title} (Vendor: ${product.vendor})`);
        }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`\n⚠️ Totale prodotti Intex da eliminare: ${toDelete.length}`);

  if (toDelete.length > 0) {
    console.log("🚀 Avvio eliminazione...");
    for (const id of toDelete) {
        const mutation = `
        mutation productDelete($input: ProductDeleteInput!) {
          productDelete(input: $input) {
            deletedProductId
            userErrors { field message }
          }
        }
        `;
        const delRes = await shopifyRequest(mutation, { input: { id } });
        if (delRes.data?.productDelete?.deletedProductId) {
            process.stdout.write(".");
        } else {
            console.error(`\n❌ Errore eliminazione ${id}:`, JSON.stringify(delRes.data?.productDelete?.userErrors));
        }
        await new Promise(r => setTimeout(r, 200));
    }
    console.log("\n✅ Eliminazione completata!");
  } else {
    console.log("✅ Nessun prodotto Intex trovato.");
  }
}

removeIntexProducts().catch(console.error);
