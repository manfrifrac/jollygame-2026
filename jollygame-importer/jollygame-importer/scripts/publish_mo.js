import dotenv from 'dotenv';
dotenv.config();

async function run() {
  const ids = [
    "gid://shopify/Metaobject/531234750812",
    "gid://shopify/Metaobject/531234783580",
    "gid://shopify/Metaobject/531234816348",
    "gid://shopify/Metaobject/531234849116"
  ];

  const mutation = `
  mutation metaobjectUpdate($id: ID!, $capabilities: MetaobjectCapabilitiesUpdateInput!) {
    metaobjectUpdate(id: $id, capabilities: $capabilities) {
      metaobject {
        id
        handle
      }
      userErrors {
        field
        message
      }
    }
  }
  `;

  for (const id of ids) {
    const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
      },
      body: JSON.stringify({ 
        query: mutation, 
        variables: { 
          id, 
          capabilities: { 
            publishable: { status: "ACTIVE" } 
          } 
        } 
      }),
    });

    const result = await response.json();
    console.log(`Published ${id}:`, JSON.stringify(result, null, 2));
  }
}

run().catch(console.error);
