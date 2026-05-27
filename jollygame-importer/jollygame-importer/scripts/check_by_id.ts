import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function checkById(id: string) {
  const query = `
    query getProduct($id: ID!) {
      product(id: $id) {
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
    body: JSON.stringify({ query, variables: { id } })
  }).then(r => r.json());

  console.log(`📂 Collezioni per ID ${id}:`);
  if (res.data?.product) {
      console.log(res.data.product.title);
      console.log(res.data.product.collections.nodes.map((c: any) => c.title));
  } else {
      console.log("Prodotto non trovato.");
  }
}

checkById("gid://shopify/Product/15527832224092").catch(console.error);
