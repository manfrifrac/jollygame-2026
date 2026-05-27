import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const query = `
  query getCollection($handle: String!) {
    collectionByHandle(handle: $handle) {
      id
      title
      productsCount
      products(first: 10) {
        nodes {
          title
          vendor
          productType
        }
      }
    }
  }
  `;

  const variables = { handle: "tutti-i-ricambi" };

  const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query, variables }),
  });

  const result = await response.json();
  if (result.errors) {
      console.error(result.errors);
  }
  console.log(JSON.stringify(result.data?.collectionByHandle || "Collection not found", null, 2));
}

run().catch(console.error);
