import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function checkPacificVariants() {
  const query = `
    query {
      product(id: "gid://shopify/Product/15527785988444") {
        title
        totalVariants
        variants(first: 10) {
          nodes {
            title
            sku
            price
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

  console.log(JSON.stringify(res.data.product, null, 2));
}

checkPacificVariants().catch(console.error);
