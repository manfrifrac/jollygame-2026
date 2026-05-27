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

async function auditDraftProducts() {
  console.log("🔍 Audit dettagliato prodotti in BOZZA...");

  let hasNextPage = true;
  let cursor = null;
  const draftDetails: any[] = [];

  while (hasNextPage) {
    const query = `
    query getDraft($cursor: String) {
      products(first: 250, after: $cursor, query: "status:draft") {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          vendor
          descriptionHtml
          mediaCount { count }
          variants(first: 5) {
            nodes {
              price
              sku
            }
          }
          metafields(first: 10, namespace: "custom") {
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
      const price = parseFloat(product.variants.nodes[0]?.price || "0");
      const sku = product.variants.nodes[0]?.sku;

      if (price <= 0) issues.push("MISSING_PRICE");
      if (!sku || sku.trim() === "") issues.push("MISSING_SKU");
      if (product.mediaCount.count === 0) issues.push("MISSING_IMAGES");
      if (!product.descriptionHtml || product.descriptionHtml.length < 20) issues.push("SHORT_DESCRIPTION");
      
      const hasSpecs = product.metafields.nodes.length > 0;
      if (!hasSpecs) issues.push("MISSING_TECH_SPECS");

      draftDetails.push({
        title: product.title,
        vendor: product.vendor,
        price: price,
        sku: sku,
        issues: issues
      });
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`\n📊 PRODOTTI IN BOZZA TROVATI: ${draftDetails.length}`);
  
  const stats = {
      missing_price: draftDetails.filter(p => p.issues.includes("MISSING_PRICE")).length,
      missing_sku: draftDetails.filter(p => p.issues.includes("MISSING_SKU")).length,
      missing_images: draftDetails.filter(p => p.issues.includes("MISSING_IMAGES")).length,
      missing_specs: draftDetails.filter(p => p.issues.includes("MISSING_TECH_SPECS")).length
  };

  console.table(stats);

  // Focus su GRE
  const greDrafts = draftDetails.filter(p => p.vendor === 'Gre');
  console.log(`\n📦 PRODOTTI GRE IN BOZZA: ${greDrafts.length}`);
  if (greDrafts.length > 0) {
      console.table(greDrafts.slice(0, 15));
  }

  fs.writeFileSync("draft_audit_report.json", JSON.stringify(draftDetails, null, 2));
}

auditDraftProducts().catch(console.error);
