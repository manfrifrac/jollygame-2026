import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const query = `{
    products(first: 250) {
      nodes {
        id
        handle
        metafields(first: 20, namespace: "custom") {
          nodes {
            key
            value
          }
        }
      }
    }
  }`;

  const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query }),
  });

  const result = await response.json();
  const products = result.data.products.nodes;
  
  const found = products.filter(p => {
      return p.metafields.nodes.some(m => m.key === "ricambi_compatibili" || m.key === "ricambi_associati");
  });

  console.log(`Found ${found.length} products with ricambi metafields:`);
  for (const p of found) {
      console.log(`- ${p.handle}: ${JSON.stringify(p.metafields.nodes.filter(m => m.key.startsWith("ricambi")))}`);
  }
}

run().catch(console.error);
