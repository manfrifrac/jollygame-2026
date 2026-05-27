import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function checkRealCollections(handle: string) {
  const query = `
    query getProduct($handle: String!) {
      product(handle: $handle) {
        title
        collections(first: 20) {
          nodes { title }
        }
      }
    }
  `;
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables: { handle } })
  }).then(r => r.json());

  console.log(`📂 Collezioni Reali per ${handle}:`);
  if (res.data?.product) {
      console.log(res.data.product.collections.nodes.map((c: any) => c.title));
  } else {
      console.log("Prodotto non trovato.");
  }
}

checkRealCollections("sirocco").catch(console.error);
