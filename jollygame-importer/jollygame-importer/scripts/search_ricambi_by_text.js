import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const query = `{
    metaobjects(first: 250, type: "ricambio") {
      nodes {
        id
        handle
        fields {
          key
          value
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
  const ricambi = result.data.metaobjects.nodes;
  
  const found = ricambi.filter(r => {
      return JSON.stringify(r.fields).toLowerCase().includes("cnx 50");
  });

  console.log(`Found ${found.length} ricambi mentioning "CNX 50":`);
  console.log(JSON.stringify(found, null, 2));
}

run().catch(console.error);
