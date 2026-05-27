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

async function runAudit() {
  console.log("🔍 Avvio Audit Qualità Catalogo (Immagini, Prezzi, Varianti)...");

  let hasNextPage = true;
  let cursor = null;
  const allProducts: any[] = [];

  while (hasNextPage) {
    const query = `
    query getProducts($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          title
          handle
          vendor
          status
          mediaCount {
            count
          }
          variants(first: 50) {
            nodes {
              id
              title
              sku
              price
              inventoryItem {
                tracked
              }
              selectedOptions {
                name
                value
              }
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (res.errors) {
      console.error("❌ Errore GraphQL:", JSON.stringify(res.errors, null, 2));
      break;
    }

    const products = res.data.products.nodes;
    allProducts.push(...products);
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
    console.log(`Fetched ${allProducts.length} products...`);
  }

  const issues = {
    missing_images: [] as any[],
    missing_price: [] as any[],
    variant_errors: [] as any[],
    missing_sku: [] as any[]
  };

  for (const product of allProducts) {
    // 1. Check Images
    if (product.mediaCount.count === 0) {
      issues.missing_images.push({
        id: product.id,
        title: product.title,
        vendor: product.vendor,
        handle: product.handle
      });
    }

    // 2. Check Prices and SKUs
    for (const variant of product.variants.nodes) {
      const priceVal = parseFloat(variant.price);
      if (isNaN(priceVal) || priceVal <= 0) {
        issues.missing_price.push({
          product_title: product.title,
          variant_title: variant.title,
          sku: variant.sku,
          price: variant.price,
          handle: product.handle
        });
      }

      if (!variant.sku || variant.sku.trim() === "") {
        issues.missing_sku.push({
            product_title: product.title,
            variant_title: variant.title,
            handle: product.handle
        });
      }

      // 3. Variant Errors (Heuristic)
      // Check for suspicious "Default Title" when there are multiple variants (shouldn't happen via API but let's check)
      if (product.variants.nodes.length > 1 && variant.title === "Default Title") {
          issues.variant_errors.push({
              product_title: product.title,
              issue: "Multipli varianti con 'Default Title'",
              handle: product.handle
          });
      }
    }

    // Check for products with many variants but potentially missing images for some? (Optional)
  }

  const report = {
    summary: {
      total_products: allProducts.length,
      missing_images_count: issues.missing_images.length,
      missing_price_count: issues.missing_price.length,
      missing_sku_count: issues.missing_sku.length,
      variant_errors_count: issues.variant_errors.length
    },
    details: issues
  };

  fs.writeFileSync("audit_quality_v2_report.json", JSON.stringify(report, null, 2));

  console.log("\n📊 RIEPILOGO AUDIT:");
  console.log(`📦 Totale Prodotti: ${allProducts.length}`);
  console.log(`🖼️ Senza Immagini: ${issues.missing_images.length}`);
  console.log(`💰 Senza Prezzo (o 0): ${issues.missing_price.length}`);
  console.log(`🆔 Senza SKU: ${issues.missing_sku.length}`);
  console.log(`⚠️ Errori Varianti: ${issues.variant_errors.length}`);
  console.log("\n✅ Report dettagliato salvato in 'audit_quality_v2_report.json'");
}

runAudit().catch(console.error);
