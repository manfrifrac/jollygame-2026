import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables = {}) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await response.json();
}

const GET_AUDIT_PRODUCTS = `
query {
  products(first: 20, sortKey: UPDATED_AT, reverse: true) {
    nodes {
      title
      vendor
      status
      descriptionHtml
      tags
      variants(first: 1) {
        nodes {
          sku
        }
      }
    }
  }
}
`;

async function main() {
  const res = await shopifyRequest(GET_AUDIT_PRODUCTS);
  const products = res.data?.products?.nodes || [];
  
  console.log("--- AUDIT QUALITÀ VENDOR E DATI ---");
  products.forEach(p => {
      console.log(`\n📦 PRODOTTO: ${p.title}`);
      console.log(`   🏷️ Vendor: ${p.vendor || 'MISSING!'}`);
      console.log(`   ✅ Status: ${p.status}`);
      console.log(`   📝 Tags: ${p.tags.join(', ')}`);
      console.log(`   📄 Descrizione HTML: ${p.descriptionHtml.substring(0, 50)}...`);
  });
}

main().catch(console.error);
