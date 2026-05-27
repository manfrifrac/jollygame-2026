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

  // ID del Prodotto (CNX-Li 52 iQ - Quello visto dall'utente)
  const product_id = "gid://shopify/Product/15546248167772";
  // ID del metaobject creato (VITE 4*12 MM)
  const ricambio_id = "gid://shopify/Metaobject/532151697756";

  const input = {
    id: product_id,
    metafields: [
      {
        namespace: "custom",
        key: "ricambi_compatibili",
        value: JSON.stringify([ricambio_id])
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
  console.log("Associazione riuscita:", JSON.stringify(result, null, 2));
}

run().catch(console.error);
