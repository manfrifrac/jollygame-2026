import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function fetchProductWithVariants() {
  // Cerchiamo prodotti che hanno più di una variante
  const query = `
    query {
      products(first: 50) {
        nodes {
          id
          title
          totalVariants
          variants(first: 20) {
            nodes {
              id
              title
              sku
              price
              selectedOptions {
                name
                value
              }
            }
          }
        }
      }
    }
  `;
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query })
  }).then(r => r.json());

  const multiVariantProducts = res.data.products.nodes.filter((p: any) => p.totalVariants > 1);
  console.log(JSON.stringify(multiVariantProducts, null, 2));
}

fetchProductWithVariants().catch(console.error);
