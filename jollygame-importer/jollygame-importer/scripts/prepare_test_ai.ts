import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function fetchProductData(id: string) {
  const query = `
    query getProduct($id: ID!) {
      product(id: $id) {
        title
        descriptionHtml
        vendor
        metafields(first: 30) {
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
    body: JSON.stringify({ query, variables: { id } })
  }).then(r => r.json());

  return res.data.product;
}

async function main() {
    const product = await fetchProductData("gid://shopify/Product/15546227917148");
    fs.writeFileSync("test_product_data.json", JSON.stringify(product, null, 2));
    console.log("✅ Dati prodotto per test recuperati.");
}

import fs from "fs";
main().catch(console.error);
