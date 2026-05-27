import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";

async function getProductDesc(id: string) {
  const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query: `{ product(id: "${id}") { title descriptionHtml } }` }),
  });
  const data = await res.json();
  console.log(`Title: ${data.data.product.title}`);
  console.log(`Desc: ${data.data.product.descriptionHtml}`);
}

getProductDesc(process.argv[2] || "gid://shopify/Product/15527758365020").catch(console.error);
