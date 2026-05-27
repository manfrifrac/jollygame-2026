import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function fetchCollections() {
  const query = `
    query {
      collections(first: 250) {
        nodes {
          id
          title
          handle
          productsCount {
            count
          }
        }
      }
    }
  `;
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query })
  }).then(r => r.json());

  if (res.errors) {
    console.error("❌ Errori GraphQL:", JSON.stringify(res.errors, null, 2));
    return;
  }

  console.log("📂 Elenco Collezioni (Tassonomia Categorie):");
  const collections = res.data.collections.nodes;
  collections.forEach((c: any) => {
      console.log(`- ${c.title} (${c.handle}) [Prodotti: ${c.productsCount.count}]`);
  });
}

fetchCollections().catch(console.error);
