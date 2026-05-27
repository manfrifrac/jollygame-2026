import dotenv from "dotenv";

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

async function deepCheckProduct(handle: string) {
  console.log(`🔍 Controllo profondo prodotto: ${handle}`);

  const query = `
  query getProduct($handle: String!) {
    productByHandle(handle: $handle) {
      id
      title
      status
      onlineStoreUrl
      resourcePublicationsV2(first: 20) {
        nodes {
          publication { name }
          isPublished
          publishDate
        }
      }
      variants(first: 10) {
        nodes {
          price
          inventoryQuantity
          availableForSale
        }
      }
    }
  }
  `;

  const res = await shopifyRequest(query, { handle });
  console.log(JSON.stringify(res.data, null, 2));
}

deepCheckProduct("pompa-di-calore-inverter-hpgic30").catch(console.error);
