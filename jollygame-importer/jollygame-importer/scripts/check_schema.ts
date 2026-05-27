import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";

const query = `
{
  products(first: 1) {
    nodes {
      id
      title
      metafields(first: 20) {
        nodes {
          namespace
          key
          value
          type
        }
      }
    }
  }
}
`;

async function checkExistingProduct() {
  const response = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN,
    },
    body: JSON.stringify({ query }),
  });

  const result: any = await response.json();
  console.log(JSON.stringify(result, null, 2));
}

checkExistingProduct().catch(console.error);
