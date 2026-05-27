import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const query = `
  query getMetaobjectByHandle($type: String!, $query: String!) {
    metaobjects(type: $type, first: 1, query: $query) {
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

  const variables = {
    type: "brand_ricambi",
    query: "handle:zodiac"
  };

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
    console.error("GraphQL Errors:", JSON.stringify(result.errors, null, 2));
    return;
  }
  console.log(JSON.stringify(result.data.metaobjects.nodes[0]?.fields || "Metaobject not found", null, 2));
}

run().catch(console.error);
