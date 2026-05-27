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

async function draftObsoleteGre() {
  const products = JSON.parse(fs.readFileSync("gre_obsolete_to_draft.json", "utf8"));
  console.log(`🛡️ Spostando ${products.length} prodotti Gre obsoleti in Bozza...`);

  let count = 0;
  for (const p of products) {
    const mutation = `
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product { id status }
        userErrors { message }
      }
    }
    `;

    const res = await shopifyRequest(mutation, {
        input: {
            id: p.id,
            status: "DRAFT"
        }
    });

    if (res.data?.productUpdate?.product) {
      count++;
      console.log(`   ✅ Drafted: ${p.title}`);
    } else {
      console.error(`   ❌ Errore ${p.id}:`, res.data?.productUpdate?.userErrors);
    }
  }

  console.log(`\n✅ Operazione completata. ${count} prodotti spostati in Bozza.`);
}

draftObsoleteGre().catch(console.error);
