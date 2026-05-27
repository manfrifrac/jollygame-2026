import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const query = `{
    metaobjects(first: 250) {
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
  if (result.errors) {
    console.error("GraphQL Errors:", JSON.stringify(result.errors, null, 2));
    return;
  }
  const allMOs = result.data.metaobjects.nodes;
  
  const targetId = "gid://shopify/Product/15546245513564";
  const found = allMOs.filter(mo => {
      return JSON.stringify(mo.fields).includes(targetId);
  });

  console.log(`Found ${found.length} metaobjects mentioning CNX 50 iQ:`);
  console.log(JSON.stringify(found, null, 2));
}

run().catch(console.error);
