import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function inspectVendorProducts(vendor: string) {
  const query = `
  query($query: String!) {
    products(first: 20, query: $query) {
      nodes {
        title
        metafields(first: 20) {
          nodes {
            namespace
            key
            value
          }
        }
      }
    }
  }
  `;

  const res = await shopifyRequest(query, { query: `vendor:'${vendor}'` });
  const products = res.data?.products?.nodes || [];
  
  console.log(`--- Ispezione Metafield Prodotti ${vendor} ---`);
  products.forEach((p: any) => {
    console.log(`\n📦 ${p.title}`);
    p.metafields.nodes.forEach((m: any) => {
      console.log(`   - ${m.namespace}.${m.key}: ${m.value}`);
    });
  });
}

async function main() {
    await inspectVendorProducts("Zodiac");
    await inspectVendorProducts("Piscine Laghetto");
}

main().catch(console.error);
