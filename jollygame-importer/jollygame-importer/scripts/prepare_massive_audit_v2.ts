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

async function prepareMassiveTargets() {
  console.log("🎯 Preparazione target massivi per audit prezzi (con recupero SKU da Shopify)...");

  const grePath = path.resolve("../../estrazione_sku_completa.csv");
  const skuToUrl = new Map();
  if (fs.existsSync(grePath)) {
    const greRecords = parse(fs.readFileSync(grePath, "utf-8"), { columns: true });
    greRecords.forEach((r: any) => skuToUrl.set(r.SKU, r.Gre_URL));
  }

  let hasNextPage = true;
  let cursor = null;
  const targets = [];

  while (hasNextPage) {
    const query = `
    query getZeroPrice($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          handle
          variants(first: 10) {
            nodes {
              id
              sku
              price
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    const products = res.data.products.nodes;
    for (const product of products) {
      for (const variant of product.variants.nodes) {
        const price = parseFloat(variant.price || "0");
        if (price === 0 && variant.sku) {
            const url = skuToUrl.get(variant.sku);
            if (url) {
                targets.push({
                    id: product.id,
                    variantId: variant.id,
                    title: product.title,
                    sku: variant.sku,
                    url: url
                });
            }
        }
      }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
    console.log(`Analizzati ${targets.length} target potenziali finora...`);
  }

  const uniqueTargets = Array.from(new Map(targets.map(t => [t.url, t])).values());

  fs.writeFileSync("price_audit_targets.json", JSON.stringify(uniqueTargets, null, 2));
  console.log(`✅ Preparati ${uniqueTargets.length} target per l'audit prezzi.`);
}

prepareMassiveTargets().catch(console.error);
