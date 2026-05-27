import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const types = ["brand_ricambi", "ricambio", "documento_tecnico"];
  const targetId = "gid://shopify/Product/15546245513564";

  for (const type of types) {
      console.log(`Checking type: ${type}...`);
      const query = `
      query getMOs($type: String!) {
        metaobjects(first: 250, type: $type) {
          nodes {
            id
            type
            handle
            fields {
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
        body: JSON.stringify({ query, variables: { type } }),
      });

      const result = await response.json();
      if (result.data && result.data.metaobjects) {
          const found = result.data.metaobjects.nodes.filter(mo => {
              return JSON.stringify(mo.fields).includes(targetId);
          });
          if (found.length > 0) {
              console.log(`Found ${found.length} in ${type}:`);
              console.log(JSON.stringify(found, null, 2));
          }
      }
  }
}

run().catch(console.error);
