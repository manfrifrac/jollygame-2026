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

const FINAL_AUDIT = `
query {
  products(first: 50, query: "status:ACTIVE") {
    nodes {
      title
      status
      variants(first: 5) {
        nodes {
          inventoryQuantity
        }
      }
      resourcePublicationsV2(first: 10) {
        nodes {
          publication { name }
          isPublished
        }
      }
    }
  }
}
`;

async function main() {
  const res = await shopifyRequest(FINAL_AUDIT);
  const products = res.data?.products?.nodes || [];
  
  console.log("--- FINAL AUDIT: STATO, CANALI, INVENTARIO ---");
  products.forEach(p => {
      const isLive = p.resourcePublicationsV2.nodes.every(n => n.isPublished);
      const stock = p.variants.nodes.reduce((acc, v) => acc + v.inventoryQuantity, 0);
      console.log(`\n📦 ${p.title}`);
      console.log(`   ✅ Status: ${p.status}`);
      console.log(`   📡 Pubblicato su tutti i canali: ${isLive ? 'SÌ' : 'NO'}`);
      console.log(`   📦 Stock totale: ${stock}`);
  });
}

main().catch(console.error);
