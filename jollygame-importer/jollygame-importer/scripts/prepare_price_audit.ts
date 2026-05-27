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

async function preparePriceAudit() {
  console.log("🔍 Identificazione prodotti con Prezzo 0...");
  
  const query = `
  query($cursor: String) {
    products(first: 250, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        title
        vendor
        variants(first: 1) {
          nodes {
            price
          }
        }
      }
    }
  }
  `;

  let hasNext = true;
  let cursor = null;
  const products: any[] = [];

  while (hasNext) {
    const res = await shopifyRequest(query, { cursor });
    products.push(...res.data.products.nodes);
    hasNext = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const zeroPriceProducts = products.filter(p => parseFloat(p.variants.nodes[0]?.price || "0") === 0);
  console.log(`💰 Trovati ${zeroPriceProducts.length} prodotti con prezzo 0.`);

  // Carico i CSV originali per recuperare gli URL
  const zodiacRecords = parse(fs.readFileSync(path.resolve("../../zodiac_enriched_data.csv"), "utf-8"), { columns: true, skip_empty_lines: true });
  const laghettoRecords = parse(fs.readFileSync(path.resolve("../../laghetto_full_export_enriched.csv"), "utf-8"), { columns: true, skip_empty_lines: true });

  const auditTargets = [];

  for (const p of zeroPriceProducts) {
      let match = zodiacRecords.find((r: any) => r.Titolo.toLowerCase().trim() === p.title.toLowerCase().trim());
      if (!match) match = laghettoRecords.find((r: any) => r.Titolo.toLowerCase().trim() === p.title.toLowerCase().trim());
      
      if (match && match.URL) {
          auditTargets.push({ id: p.id, title: p.title, url: match.URL, vendor: p.vendor });
      }
  }

  fs.writeFileSync("price_audit_targets.json", JSON.stringify(auditTargets, null, 2));
  console.log(`✅ Creato price_audit_targets.json con ${auditTargets.length} prodotti da verificare online.`);
}

preparePriceAudit().catch(console.error);
