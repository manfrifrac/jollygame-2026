import fs from "fs";
import path from "path";
import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function finalizeCatalog() {
  console.log("🚀 Inizio bonifica finale catalogo...");

  // 1. Carico i risultati dell'audit prezzi
  const auditPath = path.resolve("../../audit_results_v2.json");
  let auditData = [];
  if (fs.existsSync(auditPath)) {
      auditData = JSON.parse(fs.readFileSync(auditPath, "utf-8"));
  }
  console.log(`💰 Trovati ${auditData.length} prezzi da aggiornare.`);

  // 2. Recupero tutti i prodotti
  const query = `{
    products(first: 250) {
      nodes {
        id
        title
        handle
        mediaCount { count }
        variants(first: 1) {
          nodes {
            id
            price
            sku
          }
        }
      }
    }
  }`;
  const res = await shopifyRequest(query);
  const products = res.data.products.nodes;

  const seenNames = new Map();
  const toDelete = [];

  for (const product of products) {
    const name = product.title.toLowerCase().trim();
    
    // Logica Deduplicazione Hard
    if (seenNames.has(name)) {
      const existing = seenNames.get(name);
      // Teniamo quello con più immagini o quello che ha uno SKU
      if (product.mediaCount.count > existing.mediaCount.count || (product.variants.nodes[0]?.sku && !existing.variants.nodes[0]?.sku)) {
          toDelete.push(existing.id);
          seenNames.set(name, product);
      } else {
          toDelete.push(product.id);
      }
    } else {
      seenNames.set(name, product);
    }

    // Logica Aggiornamento Prezzo (se presente nell'audit)
    const auditMatch = auditData.find((a: any) => a.title.toLowerCase().trim() === name);
    if (auditMatch && auditMatch.new_price && auditMatch.new_price !== "0.00") {
        const variantId = product.variants.nodes[0].id;
        let cleanPrice = auditMatch.new_price.replace(/[^\d.,]/g, "").replace(",", ".");
        
        console.log(`  💲 Aggiornamento prezzo per [${product.title}]: €${cleanPrice}`);
        await shopifyRequest(`
          mutation productVariantUpdate($input: ProductVariantInput!) {
            productVariantUpdate(input: $input) {
              productVariant { id price }
              userErrors { message }
            }
          }
        `, { input: { id: variantId, price: cleanPrice } });
    }
  }

  // 3. Eseguo eliminazioni duplicati
  if (toDelete.length > 0) {
    console.log(`\n🗑️ Eliminazione di ${toDelete.length} duplicati residui...`);
    for (const id of toDelete) {
        await shopifyRequest(`mutation { productDelete(input: { id: "${id}" }) { deletedProductId } }`);
        process.stdout.write(".");
    }
  }

  console.log("\n\n✅ Prezzi aggiornati e duplicati rimossi.");
}

finalizeCatalog().catch(console.error);
