import dotenv from "dotenv";
import fs from "fs";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function deleteKits() {
  const data = JSON.parse(fs.readFileSync("master_catalog_dump.json", "utf8"));
  const toDelete = data.filter((p: any) => p.title.startsWith("KIT Piscina ovale") || p.title.startsWith("KIT Piscina tonda"));
  
  console.log(`🗑️ Eliminazione di ${toDelete.length} kit individuali...`);
  
  for (const p of toDelete) {
    console.log(` - Eliminando: ${p.title}`);
    const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN!
      },
      body: JSON.stringify({
        query: `mutation { productDelete(input: { id: "${p.id}" }) { deletedProductId } }`
      })
    });
  }
  console.log("✅ Fatto.");
}

deleteKits().catch(console.error);
