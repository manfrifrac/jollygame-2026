import dotenv from "dotenv";
import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await response.json();
}

async function getMissingImageUrls() {
  console.log("🔍 Identificazione prodotti senza immagini...");
  
  const query = `{
    products(first: 250) {
      nodes {
        id
        title
        handle
        vendor
        mediaCount { count }
      }
    }
  }`;

  const res = await shopifyRequest(query);
  const products = res.data.products.nodes.filter((p: any) => p.mediaCount.count === 0 && p.vendor === "Zodiac");
  
  console.log(`🔎 Trovati ${products.length} prodotti Zodiac senza immagini.`);

  const csvPath = path.resolve("../../zodiac_enriched_data.csv");
  const records = parse(fs.readFileSync(csvPath, "utf-8"), { columns: true, skip_empty_lines: true });

  const targets = [];
  for (const product of products) {
      const match = records.find((r: any) => r.Titolo.toLowerCase().trim() === product.title.toLowerCase().trim());
      if (match && match.URL) {
          targets.push({ title: product.title, url: match.URL });
      }
  }

  fs.writeFileSync("missing_images_targets.json", JSON.stringify(targets, null, 2));
  console.log(`✅ Creato missing_images_targets.json con ${targets.length} URL da scansionare.`);
}

getMissingImageUrls().catch(console.error);
