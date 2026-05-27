import fs from 'fs';
import dotenv from 'dotenv';
import fetch from 'node-fetch';

const envPath = '.env';
const envConfig = dotenv.parse(fs.readFileSync(envPath));

async function getVendors() {
  const query = `
    query {
      productVendors(first: 50) {
        edges {
          node
        }
      }
    }
  `;

  const response = await fetch(`https://${envConfig.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': envConfig.SHOPIFY_ACCESS_TOKEN
    },
    body: JSON.stringify({ query })
  });

  const data = await response.json();
  if (data.errors) {
    console.error(JSON.stringify(data.errors, null, 2));
  } else {
    console.log(JSON.stringify(data.data.productVendors.edges.map(e => e.node), null, 2));
  }
}

getVendors();
