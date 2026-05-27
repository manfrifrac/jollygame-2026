import dotenv from 'dotenv';
dotenv.config();

async function run() {
  const query = `
  {
    __type(name: "MetaobjectCapabilityOnlineStoreInput") {
      inputFields {
        name
        type {
          name
          kind
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
    body: JSON.stringify({ query }),
  });

  const result = await response.json();
  console.log(JSON.stringify(result.data.__type.inputFields, null, 2));
}

run().catch(console.error);
