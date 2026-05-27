import dotenv from "dotenv";
import fs from "fs";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const THEME_ID = "196636049756";

async function uploadSection() {
  console.log(`📤 Uploading main-product.liquid to theme ${THEME_ID}...`);

  const content = fs.readFileSync("theme_tmp/sections/main-product.liquid", "utf8");

  const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/themes/${THEME_ID}/assets.json`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({
      asset: {
        key: "sections/main-product.liquid",
        value: content
      }
    }),
  });

  const data = await res.json();
  console.log(JSON.stringify(data, null, 2));
}

uploadSection().catch(console.error);
