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

async function auditVariants() {
  console.log("🔍 Avvio Audit Varianti Prodotti...");

  let hasNextPage = true;
  let cursor = null;
  const variantReport: any[] = [];

  while (hasNextPage) {
    const query = `
    query getProducts($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          status
          variants(first: 20) {
            nodes {
              id
              title
              sku
              price
              inventoryQuantity
              availableForSale
              sellableOnlineQuantity
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
      if (product.variants.nodes.length > 1) {
          const issues: string[] = [];
          const variants = product.variants.nodes;

          const zeroPriceVariants = variants.filter((v: any) => parseFloat(v.price) <= 0);
          const outOfStockVariants = variants.filter((v: any) => v.inventoryQuantity <= 0);
          const unavailableVariants = variants.filter((v: any) => !v.availableForSale);

          if (zeroPriceVariants.length > 0) issues.push(`${zeroPriceVariants.length} varianti a prezzo 0`);
          if (unavailableVariants.length > 0) issues.push(`${unavailableVariants.length} varianti non disponibili alla vendita`);

          variantReport.push({
            title: product.title,
            status: product.status,
            total_variants: variants.length,
            issues: issues,
            variant_details: variants.map((v: any) => ({
                name: v.title,
                price: v.price,
                stock: v.inventoryQuantity,
                available: v.availableForSale
            }))
          });
      }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const flagged = variantReport.filter(r => r.issues.length > 0);

  console.log(`\n📊 RISULTATI AUDIT VARIANTI:`);
  console.log(`✅ Prodotti con varianti ok: ${variantReport.length - flagged.length}`);
  console.log(`⚠️  Prodotti con problemi nelle varianti: ${flagged.length}`);

  if (flagged.length > 0) {
      console.log("\n❌ DETTAGLIO PROBLEMI VARIANTI:");
      console.table(flagged.slice(0, 15).map(f => ({
          Prodotto: f.title,
          Varianti: f.total_variants,
          Problemi: f.issues.join(", ")
      })));
  }

  fs.writeFileSync("variant_audit_report.json", JSON.stringify(variantReport, null, 2));
}

auditVariants().catch(console.error);
