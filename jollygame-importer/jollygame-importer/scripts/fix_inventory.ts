import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables = {}) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await response.json();
}

// 1. Get all variants and their InventoryItem IDs
const GET_ALL_VARIANTS = `
query {
  products(first: 250, query: "status:ACTIVE") {
    nodes {
      variants(first: 10) {
        nodes {
          id
          inventoryItem {
            id
          }
        }
      }
    }
  }
}
`;

// 2. Mutation to set inventory
const ADJUST_INVENTORY = `
mutation inventoryAdjust($input: InventoryAdjustQuantityInput!) {
  inventoryAdjustQuantity(input: $input) {
    inventoryLevel {
      id
      available
    }
    userErrors { message }
  }
}
`;

async function main() {
    const res = await shopifyRequest(GET_ALL_VARIANTS);
    const products = res.data?.products?.nodes || [];
    
    // First, let's get the location ID (required for inventory updates)
    const LOCATIONS = await shopifyRequest(`query { locations(first: 1) { nodes { id } } }`);
    const locationId = LOCATIONS.data?.locations?.nodes[0]?.id;

    console.log(`📍 Locazione trovata: ${locationId}`);

    for (const p of products) {
        for (const v of p.variants.nodes) {
            const invItemId = v.inventoryItem.id;
            console.log(`📦 Aggiorno ${invItemId} a 10 unità...`);
            
            await shopifyRequest(ADJUST_INVENTORY, {
                input: {
                    inventoryItemId: invItemId,
                    locationId: locationId,
                    availableAdjustment: 10
                }
            });
        }
    }
    console.log("✅ Inventario aggiornato!");
}

main().catch(console.error);
