import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const query = `
  query getMO($id: ID!) {
    metaobject(id: $id) {
      id
      type
      handle
      fields {
        key
        value
        reference {
          __typename
          ... on Product {
            id
            title
          }
        }
      }
    }
  }
  `;

  const variables = { id: "gid://shopify/Metaobject/532151697756" };

  const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query, variables }),
  });

  const result = await response.json();
  console.log(JSON.stringify(result, null, 2));
}

run().catch(console.error);
