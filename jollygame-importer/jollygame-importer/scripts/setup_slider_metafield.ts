import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
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

async function setupListMetafield() {
  console.log("🚀 Creazione Metafield Lista Prodotti (per Slider)...");

  const createMetafieldQuery = `
  mutation {
    metafieldDefinitionCreate(definition: {
      name: "Lista Prodotti Menu (Slider)"
      namespace: "custom"
      key: "featured_products_list"
      ownerType: COLLECTION
      type: "list.product_reference"
      description: "Seleziona almeno 3 prodotti per lo slider del Mega Menu."
    }) {
      createdDefinition {
        id
        name
      }
      userErrors {
        field
        message
      }
    }
  }
  `;

  const res = await shopifyRequest(createMetafieldQuery);
  if (res.data?.metafieldDefinitionCreate?.createdDefinition) {
    console.log("✅ Metafield 'custom.featured_products_list' creato.");
  } else {
    console.log("ℹ️ Nota:", res.data?.metafieldDefinitionCreate?.userErrors[0]?.message || "Gia esistente");
  }
}

setupListMetafield().catch(console.error);
