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

async function auditPoolVariants() {
  console.log("🔍 Audit approfondito varianti categoria PISCINE...");

  let hasNextPage = true;
  let cursor = null;
  const poolVariantReport: any[] = [];

  while (hasNextPage) {
    const query = `
    query getPools($cursor: String) {
      products(first: 250, after: $cursor, query: "tag:'Categoria:Piscine'") {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          status
          vendor
          variants(first: 50) {
            nodes {
              id
              title
              sku
              price
              inventoryQuantity
              availableForSale
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
        const variants = product.variants.nodes;
        const issues: string[] = [];

        const zeroPrice = variants.filter((v: any) => parseFloat(v.price) <= 0);
        const noSku = variants.filter((v: any) => !v.sku);
        const unavailable = variants.filter((v: any) => !v.availableForSale);

        if (zeroPrice.length > 0) issues.push(`${zeroPrice.length} varianti con prezzo 0`);
        if (noSku.length > 0) issues.push(`${noSku.length} varianti senza SKU`);
        if (unavailable.length > 0) issues.push(`${unavailable.length} varianti non vendibili`);

        poolVariantReport.push({
            title: product.title,
            vendor: product.vendor,
            status: product.status,
            total_variants: variants.length,
            issues: issues,
            variant_details: variants.map((v: any) => ({
                name: v.title,
                sku: v.sku,
                price: v.price,
                stock: v.inventoryQuantity,
                available: v.availableForSale
            }))
        });
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const flagged = poolVariantReport.filter(r => r.issues.length > 0);
  console.log(`\n📊 RISULTATI AUDIT PISCINE:`);
  console.log(`✅ Piscine con varianti ok: ${poolVariantReport.length - flagged.length}`);
  console.log(`⚠️  Piscine con problemi varianti: ${flagged.length}`);

  if (flagged.length > 0) {
      console.log("\n❌ DETTAGLIO PROBLEMI PISCINE:");
      console.table(flagged.map(f => ({
          Piscina: f.title.substring(0, 40),
          Varianti: f.total_variants,
          Problemi: f.issues.join(", "),
          Stato: f.status
      })));
  }

  fs.writeFileSync("pool_variants_audit.json", JSON.stringify(poolVariantReport, null, 2));
}

auditPoolVariants().catch(console.error);
