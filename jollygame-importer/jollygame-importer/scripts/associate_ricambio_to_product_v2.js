import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const mutation = `
  mutation productUpdate($input: ProductInput!) {
    productUpdate(input: $input) {
      product { id }
      userErrors { field message }
    }
  }
  `;

  // ID del Metaobject creato in precedenza (test)
  const metaobject_id = "gid://shopify/Metaobject/531765690716";
  const product_id = "gid://shopify/Product/15527758365020";

  // Aggiorniamo il metafield del prodotto usando il namespace/key corretti
  const input = {
    id: product_id,
    metafields: [
      {
        namespace: "custom",
        key: "ricambi_associati",
        value: JSON.stringify([metaobject_id])
      }
    ]
  };

  const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query: mutation, variables: { input } }),
  });

  const result = await response.json();
  console.log("Risultato Update:", JSON.stringify(result, null, 2));
}

run().catch(console.error);
