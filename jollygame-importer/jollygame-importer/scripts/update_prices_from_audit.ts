import dotenv from "dotenv";
import fs from "fs";
import path from "path";

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

const PRODUCT_VARIANTS_BULK_UPDATE = `
mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId: $productId, variants: $variants) {
    productVariants {
      id
      price
    }
    userErrors {
      field
      message
    }
  }
}
`;

const GET_PRODUCT_VARIANTS = `
query getProductVariants($id: ID!) {
  product(id: $id) {
    variants(first: 10) {
      nodes {
        id
        title
      }
    }
  }
}
`;

async function updatePrices() {
  console.log("💰 Avvio aggiornamento prezzi da audit_results_v2.json...");

  const auditPath = path.resolve("../../audit_results_v2.json");
  if (!fs.existsSync(auditPath)) {
    console.error("❌ File audit_results_v2.json non trovato.");
    return;
  }

  const auditData = JSON.parse(fs.readFileSync(auditPath, "utf-8"));
  let updatedCount = 0;

  for (const item of auditData) {
    if (item.new_price && item.id) {
      console.log(`\n🏷️  Aggiornamento: ${item.title} -> €${item.new_price}`);
      
      // Pulizia prezzo (es. "1.962" -> "1962.00")
      const cleanPrice = item.new_price.replace(".", "").replace(",", ".");
      
      // Recupero varianti per il prodotto
      const varRes = await shopifyRequest(GET_PRODUCT_VARIANTS, { id: item.id });
      const variants = varRes.data?.product?.variants?.nodes || [];

      if (variants.length === 0) {
        console.warn(`  ⚠️ Nessuna variante trovata per ${item.title}`);
        continue;
      }

      // Prepariamo l'input per il bulk update
      const variantInputs = variants.map((v: any) => ({
        id: v.id,
        price: cleanPrice
      }));

      const updateRes = await shopifyRequest(PRODUCT_VARIANTS_BULK_UPDATE, {
        productId: item.id,
        variants: variantInputs
      });

      if (updateRes.data?.productVariantsBulkUpdate?.productVariants) {
        console.log(`  ✅ ${variants.length} varianti aggiornate a €${cleanPrice}`);
        updatedCount += variants.length;
      } else {
        console.error(`  ❌ Errore aggiornamento varianti:`, JSON.stringify(updateRes.errors || updateRes.data?.productVariantsBulkUpdate?.userErrors));
      }
      
      await new Promise(r => setTimeout(r, 500)); // Rate limiting preventivo
    }
  }

  console.log(`\n✅ Aggiornamento completato! Totale varianti aggiornate: ${updatedCount}`);
}

updatePrices().catch(console.error);
