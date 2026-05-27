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

const AUDIT_QUERY = `
query {
  products(first: 20, sortKey: UPDATED_AT, reverse: true) {
    nodes {
      title
      tags
      collections(first: 10) {
        nodes {
          title
        }
      }
    }
  }
}
`;

async function main() {
  const res = await shopifyRequest(AUDIT_QUERY);
  const products = res.data?.products?.nodes || [];
  
  console.log("--- AUDIT DETTAGLIATO: PRODOTTI vs COLLEZIONI ---");
  products.forEach(p => {
      const colls = p.collections.nodes.map(c => c.title).join(", ");
      console.log(`\n📦 PRODOTTO: ${p.title}`);
      console.log(`   🏷️ Tags: ${p.tags.join(', ')}`);
      console.log(`   📂 Assegnato alle collezioni: ${colls}`);
  });
}

main().catch(console.error);
