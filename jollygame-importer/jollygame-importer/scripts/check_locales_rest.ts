import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";

async function checkLocales() {
  const restUrl = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/shop_locales.json`;
  const res = await fetch(restUrl, {
    headers: { "X-Shopify-Access-Token": ACCESS_TOKEN! }
  });
  const data = await res.json();
  console.log(JSON.stringify(data, null, 2));
}

checkLocales().catch(console.error);
