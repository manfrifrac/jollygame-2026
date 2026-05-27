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

  // ID del prodotto (CNX 50 iQ)
  const product_id = "gid://shopify/Product/15527758365020";
  // ID del metaobject creato (Ricambio)
  const ricambio_id = "gid://shopify/Metaobject/531765690716";

  // Per creare un collegamento Metafield di tipo "List of Metaobjects"
  // dobbiamo passare gli ID dei Metaobject nell'array
  const input = {
    id: product_id,
    metafields: [
      {
        namespace: "custom",
        key: "ricambi_compatibili",
        type: "list.metaobject_reference",
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
  console.log("Risultato Update:", JSON.stringify(result, null, 2));
}

run().catch(console.error);
