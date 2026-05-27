import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const mutation = `
  mutation metaobjectUpdate($id: ID!, $metaobject: MetaobjectUpdateInput!) {
    metaobjectUpdate(id: $id, metaobject: $metaobject) {
      metaobject { id }
      userErrors { field message }
    }
  }
  `;

  // Lista ID dei metaobject creati
  const ids = [
    "gid://shopify/Metaobject/531758547292",
    "gid://shopify/Metaobject/531765690716"
  ];

  for (const id of ids) {
    const metaobject = {
      capabilities: {
        publishable: { status: "ACTIVE" }
      }
    };

    const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
      },
      body: JSON.stringify({ query: mutation, variables: { id, metaobject } }),
    });

    const result = await response.json();
    console.log(`Pubblicazione ${id}:`, JSON.stringify(result, null, 2));
  }
}

run().catch(console.error);
