import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function countByTag(tag: string) {
  const query = `{ products(first: 250, query: "tag:'${tag}'") { nodes { title } } }`;
  const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query }),
  });
  const data = await res.json();
  console.log(`Tag: ${tag} | Count: ${data.data?.products?.nodes.length || 0}`);
}

const API_VERSION = "2024-10";
countByTag("Sottocategoria:Piscine in acciaio").catch(console.error);
countByTag("Categoria:Piscine").catch(console.error);
