import dotenv from "dotenv";
import fs from "fs";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function exportGreDraftsForScraping() {
  console.log("📤 Esportazione prodotti Gre in Bozza per mappatura...");

  const query = `
  {
    products(first: 250, query: "status:draft vendor:Gre") {
      nodes {
        id
        title
        handle
        variants(first: 1) { nodes { sku price } }
      }
    }
  }
  `;

  const res = await shopifyRequest(query);
  const products = res.data?.products?.nodes || [];

  const exportData = products.map((p: any) => ({
      id: p.id,
      title: p.title,
      handle: p.handle,
      sku: p.variants.nodes[0]?.sku || null,
      current_price: p.variants.nodes[0]?.price || "0"
  }));

  fs.writeFileSync("gre_drafts_to_scrape.json", JSON.stringify(exportData, null, 2));
  console.log(`✅ Esportati ${exportData.length} prodotti in 'gre_drafts_to_scrape.json'`);
}

exportGreDraftsForScraping().catch(console.error);
