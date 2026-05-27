import dotenv from 'dotenv';
dotenv.config();

async function run() {
  const query = `{
    metaobjects(first: 5, type: "brand_ricambi") {
      nodes {
        id
        handle
        type
        updatedAt
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
  console.log(JSON.stringify(result.data.metaobjects.nodes, null, 2));
}

run().catch(console.error);
