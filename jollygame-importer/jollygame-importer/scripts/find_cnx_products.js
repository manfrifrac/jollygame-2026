import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const query = `{
    products(first: 50, query: "title:CNX") {
      nodes {
        id
        title
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
  console.log(JSON.stringify(result.data.products.nodes, null, 2));
}

run().catch(console.error);
