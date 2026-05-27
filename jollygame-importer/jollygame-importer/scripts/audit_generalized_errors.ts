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

async function runGeneralizedAudit() {
  console.log("🚀 Avvio Audit Errori Generalizzati...");

  let hasNextPage = true;
  let cursor = null;
  const errorReport: any[] = [];

  while (hasNextPage) {
    const query = `
    query getProducts($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          handle
          status
          vendor
          descriptionHtml
          mediaCount { count }
          variants(first: 10) {
            nodes {
              id
              price
              sku
            }
          }
          metafields(first: 20, namespace: "custom") {
            nodes {
              key
              value
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
      const issues: string[] = [];

      // 1. AI Leakage in Title
      const aiPatterns = ["->", "diventa", "nuovo titolo", "riscrivilo", "ottimizzato", "null", "titolo:"];
      if (aiPatterns.some(p => product.title.toLowerCase().includes(p))) {
        issues.push("AI_LEAKAGE_TITLE");
      }

      // 2. AI Leakage in Description
      if (product.descriptionHtml && aiPatterns.some(p => product.descriptionHtml.toLowerCase().includes(p))) {
        issues.push("AI_LEAKAGE_DESCRIPTION");
      }

      // 3. Zero Price on Active Product
      const hasZeroPrice = product.variants.nodes.some((v: any) => parseFloat(v.price) <= 0);
      if (product.status === "ACTIVE" && hasZeroPrice) {
        issues.push("ZERO_PRICE_ACTIVE");
      }

      // 4. Missing SKU
      const missingSku = product.variants.nodes.some((v: any) => !v.sku || v.sku.trim() === "");
      if (missingSku) {
        issues.push("MISSING_SKU");
      }

      // 5. Missing Images
      if (product.mediaCount.count === 0) {
        issues.push("MISSING_IMAGES");
      }

      // 6. Broken Handle (Check if handle contains 'undefined')
      if (product.handle.includes("undefined")) {
        issues.push("BROKEN_HANDLE");
      }

      if (issues.length > 0) {
        errorReport.push({
          id: product.id,
          title: product.title,
          handle: product.handle,
          vendor: product.vendor,
          issues: issues
        });
      }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const summary = {
    total_flagged: errorReport.length,
    by_issue: {
      AI_LEAKAGE_TITLE: errorReport.filter(p => p.issues.includes("AI_LEAKAGE_TITLE")).length,
      AI_LEAKAGE_DESCRIPTION: errorReport.filter(p => p.issues.includes("AI_LEAKAGE_DESCRIPTION")).length,
      ZERO_PRICE_ACTIVE: errorReport.filter(p => p.issues.includes("ZERO_PRICE_ACTIVE")).length,
      MISSING_SKU: errorReport.filter(p => p.issues.includes("MISSING_SKU")).length,
      MISSING_IMAGES: errorReport.filter(p => p.issues.includes("MISSING_IMAGES")).length,
      BROKEN_HANDLE: errorReport.filter(p => p.issues.includes("BROKEN_HANDLE")).length
    }
  };

  console.log("\n📊 RIEPILOGO ERRORI TROVATI:");
  console.table(summary.by_issue);

  fs.writeFileSync("generalized_errors_report.json", JSON.stringify({ summary, details: errorReport }, null, 2));
  console.log("\n✅ Report salvato in 'generalized_errors_report.json'");
  
  // Stampa i primi 5 casi di AI Leakage per conferma visiva
  const aiCases = errorReport.filter(p => p.issues.includes("AI_LEAKAGE_TITLE")).slice(0, 5);
  if (aiCases.length > 0) {
      console.log("\n⚠️ ESEMPI DI AI LEAKAGE NEI TITOLI:");
      aiCases.forEach(c => console.log(` - ${c.title}`));
  }
}

runGeneralizedAudit().catch(console.error);
