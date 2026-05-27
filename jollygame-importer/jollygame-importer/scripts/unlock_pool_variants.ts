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

async function unlockPoolVariants() {
  console.log("🔓 Sblocco magazzino per tutte le varianti PISCINE...");

  const query = `{
    products(first: 250, query: "tag:'Categoria:Piscine' status:active") {
      nodes {
        id
        title
        variants(first: 50) {
          nodes {
            id
            inventoryQuantity
            inventoryPolicy
          }
        }
      }
    }
  }`;

  const res = await shopifyRequest(query);
  const products = res.data?.products?.nodes || [];

  let totalUnlocked = 0;

  for (const product of products) {
      const variantsToUpdate = product.variants.nodes.filter((v: any) => v.inventoryPolicy !== "CONTINUE");
      
      if (variantsToUpdate.length > 0) {
          console.log(`📦 Sblocco: ${product.title} (${variantsToUpdate.length} varianti)`);
          
          const mutation = `
          mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
            productVariantsBulkUpdate(productId: $productId, variants: $variants) {
              product { id }
              userErrors { field message }
            }
          }
          `;

          const variantInputs = variantsToUpdate.map((v: any) => ({
              id: v.id,
              inventoryPolicy: "CONTINUE"
          }));

          const updateRes = await shopifyRequest(mutation, {
              productId: product.id,
              variants: variantInputs
          });

          if (!updateRes.data?.productVariantsBulkUpdate?.userErrors?.length) {
              totalUnlocked += variantsToUpdate.length;
          } else {
              console.error(`❌ Errore sblocco ${product.title}:`, updateRes.data.productVariantsBulkUpdate.userErrors);
          }
      }
  }

  console.log(`\n✅ Operazione completata. ${totalUnlocked} varianti piscina ora sempre disponibili.`);
}

unlockPoolVariants().catch(console.error);
