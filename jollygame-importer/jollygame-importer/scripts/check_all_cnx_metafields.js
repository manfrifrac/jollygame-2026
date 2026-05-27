import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const handles = ["cnx-50-iq", "cnx-50-iq-1", "cnx-50-iq-2"];

  for (const handle of handles) {
    console.log(`Checking handle: ${handle}...`);
    const query = `
    query getProduct($handle: String!) {
      productByHandle(handle: $handle) {
        id
        title
        metafields(first: 20, namespace: "custom") {
          nodes {
            key
            value
          }
        }
      }
    }
    `;

    const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
      },
      body: JSON.stringify({ query, variables: { handle } }),
    });

    const result = await response.json();
    console.log(JSON.stringify(result, null, 2));
  }
}

run().catch(console.error);
