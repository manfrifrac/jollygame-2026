import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function checkProductCollections(handle: string) {
  const query = `
    query getProduct($handle: String!) {
      product(handle: $handle) {
        title
        collections(first: 5) {
          nodes {
            title
            handle
          }
        }
      }
    }
  `;
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables: { handle } })
  }).then(r => r.json());

  console.log(`📂 Collezioni per: ${handle}`);
  if (res.data?.product) {
      console.log(JSON.stringify(res.data.product.collections.nodes, null, 2));
  } else {
      console.log("Prodotto non trovato o errore.");
  }
}

async function main() {
    // Proviamo con un robot e una piscina
    await checkProductCollections("aspirapolvere-ra-6300-iq");
    await checkProductCollections("pompe-di-calore-inverter-hpgic30");
}

main().catch(console.error);
