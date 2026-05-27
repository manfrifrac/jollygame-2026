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

async function importMissingGre() {
  const products = JSON.parse(fs.readFileSync("new_gre_products_to_import.json", "utf8"));
  console.log(`🚀 Inizio importazione di ${products.length} nuovi prodotti Gre...`);

  let count = 0;
  for (const p of products) {
    // 1. Create Product
    const createMutation = `
    mutation productCreate($product: ProductCreateInput!) {
      productCreate(product: $product) {
        product { id title variants(first: 1) { nodes { id } } }
        userErrors { field message }
      }
    }
    `;

    const productInput = {
      title: p.title,
      descriptionHtml: p.description,
      vendor: "Gre",
      status: "DRAFT",
      productType: p.taxonomy || "Gre",
      tags: ["Brand:Gre", "Listino:2026"]
    };

    const createRes = await shopifyRequest(createMutation, { product: productInput });
    const product = createRes.data?.productCreate?.product;
    
    if (product) {
      const variantId = product.variants.nodes[0].id;
      
      // 2. Update Variant with SKU and Price
      const variantMutation = `
      mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
        productVariantsBulkUpdate(productId: $productId, variants: $variants) {
          product { id }
          userErrors { field message }
        }
      }
      `;

      await shopifyRequest(variantMutation, {
          productId: product.id,
          variants: [
              {
                  id: variantId,
                  sku: p.sku,
                  price: p.price.toString(),
                  inventoryPolicy: "CONTINUE"
              }
          ]
      });

      count++;
      if (count % 20 === 0) console.log(`   - Creati ${count} prodotti...`);
    } else {
      console.error(`❌ Errore creazione ${p.sku}:`, JSON.stringify(createRes.data?.productCreate?.userErrors, null, 2));
    }
  }

  console.log(`\n✅ Importazione completata! ${count} prodotti aggiunti in Bozza.`);
}

importMissingGre().catch(console.error);
