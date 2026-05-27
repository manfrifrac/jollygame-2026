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

const PRODUCT_VARIANTS_BULK_UPDATE = `
mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId: $productId, variants: $variants) {
    productVariants { id price }
    userErrors { field message }
  }
}
`;

async function applyFinalPriorityPrices() {
  const finalPrices: Record<string, string> = {
    // Robot
    "RA 6800 iQ": "1849.00",
    "RA 6300 iQ": "1962.00",
    "TRX 8500 iQ": "3990.00",
    "TRX 8700 iQ": "4790.00",
    "E30iQ": "1249.00",
    
    // Pompe Calore
    "Z400iQ": "3200.00",
    "Z250iQ": "1450.00",
    "Z350iQ": "1950.00",
    "Z650iQ": "4200.00",
    "Z550iQ": "2800.00",
    "Power Force Inverter": "6900.00",
    "Z950 Inverter": "5500.00",
    
    // Trattamento
    "eXO® iQ": "1550.00",
    "eXO® iQ LS": "1650.00",
    "Ei² iQ": "990.00",
    "EiSalt": "750.00",
    "iQPump": "1050.00",
    "pH Expert": "420.00",
    "Chlor Expert": "480.00",
    
    // Intex / Altro
    "Piscina Rettangolare Ultra Xtr Frame 975x488x132cm": "1690.00",
    "Piscina Intex Graphite Rotonda Con Pompa Filtro E Scaletta": "1190.00"
  };

  console.log("💰 Applicazione prezzi finali prodotti di punta...");

  const query = `
    query {
      products(first: 250) {
        nodes {
          id
          title
          variants(first: 50) {
            nodes {
              id
              sku
            }
          }
        }
      }
    }
  `;

  const res = await shopifyRequest(query);
  const products = res.data?.products?.nodes || [];

  for (const product of products) {
    const variantUpdates = [];
    
    // Cerchiamo corrispondenza esatta o fuzzy nel titolo per i prodotti di punta
    for (const [targetTitle, price] of Object.entries(finalPrices)) {
        if (product.title.includes(targetTitle)) {
            for (const variant of product.variants.nodes) {
                variantUpdates.push({
                    id: variant.id,
                    price: price
                });
            }
            break; 
        }
    }

    if (variantUpdates.length > 0) {
      console.log(`🏷️ Aggiornamento prezzi per "${product.title}" (${product.id})...`);
      const updateRes = await shopifyRequest(PRODUCT_VARIANTS_BULK_UPDATE, {
        productId: product.id,
        variants: variantUpdates
      });
      if (updateRes.data?.productVariantsBulkUpdate?.productVariants) {
        console.log(`  ✅ ${variantUpdates.length} varianti aggiornate.`);
      } else {
        console.error(`  ❌ Errore:`, JSON.stringify(updateRes.data?.productVariantsBulkUpdate?.userErrors));
      }
    }
  }
}

applyFinalPriorityPrices().catch(console.error);
