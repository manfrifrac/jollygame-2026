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

async function fullVariantAudit() {
  console.log("🔍 Avvio Audit Completo Prezzi e Magazzino Varianti...");

  let hasNextPage = true;
  let cursor = null;
  const issues: any[] = [];

  while (hasNextPage) {
    const query = `
    query getVariants($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          title
          status
          variants(first: 50) {
            nodes {
              title
              sku
              price
              inventoryQuantity
              inventoryItem { tracked }
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
        for (const v of product.variants.nodes) {
            const price = parseFloat(v.price);
            const stock = v.inventoryQuantity;
            
            if (price <= 0 || stock <= 0 || !v.availableForSale) {
                issues.push({
                    product: product.title,
                    variant: v.title,
                    sku: v.sku,
                    price: price,
                    stock: stock,
                    tracked: v.inventoryItem?.tracked,
                    available: v.availableForSale,
                    status: product.status
                });
            }
        }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`\n📊 REPORT VARIANTI PROBLEMATICHE:`);
  console.log(`❌ Totale varianti con problemi (Prezzo 0 o Stock 0): ${issues.length}`);
  
  const zeroPrice = issues.filter(i => i.price <= 0).length;
  const zeroStock = issues.filter(i => i.stock <= 0).length;

  console.log(`💰 Varianti a Prezzo 0: ${zeroPrice}`);
  console.log(`📦 Varianti a Stock 0: ${zeroStock}`);

  // Esempi
  console.log("\n📝 Esempi di varianti bloccate:");
  console.table(issues.slice(0, 20).map(i => ({
      Prodotto: i.product.substring(0, 30),
      Variante: i.variant,
      Prezzo: i.price,
      Stock: i.stock,
      Disponibile: i.available
  })));

  fs.writeFileSync("full_variant_issues.json", JSON.stringify(issues, null, 2));
  console.log("\n✅ Report completo salvato in 'full_variant_issues.json'");
}

fullVariantAudit().catch(console.error);
