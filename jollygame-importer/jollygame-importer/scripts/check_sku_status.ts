import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function checkSku(sku: string) {
  const query = `{ products(first:1, query: "sku:${sku}") { nodes { id title status variants(first:1) { nodes { id price } } } } }`;
  const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query }),
  });
  const data = await res.json();
  console.log(JSON.stringify(data.data.products.nodes[0], null, 2));
}

checkSku(process.argv[2]).catch(console.error);
