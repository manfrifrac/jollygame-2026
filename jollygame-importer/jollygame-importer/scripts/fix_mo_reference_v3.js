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

  // ID del Metaobject e del prodotto
  const id = "gid://shopify/Metaobject/531765690716";
  const product_id = "gid://shopify/Product/15527758365020";

  // Per i campi 'list.product_reference', l'input deve essere un array di GID stringhe
  const metaobject = {
    fields: [
      { key: "prodotti_correlati", value: JSON.stringify([product_id]) }
    ]
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
  console.log("Risultato Update:", JSON.stringify(result, null, 2));
}

run().catch(console.error);
