import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function checkProductTaxonomy(handle: string) {
  const query = `
    query getProduct($handle: String!) {
      product(handle: $handle) {
        title
        metafields(first: 20) {
          nodes {
            key
            value
            namespace
          }
        }
      }
    }
  `;
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables: { handle } })
  }).then(r => r.json());

  console.log(`📊 Tassonomia per: ${handle}`);
  console.log(JSON.stringify(res.data.product.metafields.nodes, null, 2));
}

// Controlliamo un paio di prodotti diversi
async function main() {
    await checkProductTaxonomy("piscina-ovale-pacific");
    await checkProductTaxonomy("ra-6300-iq");
}

main().catch(console.error);
