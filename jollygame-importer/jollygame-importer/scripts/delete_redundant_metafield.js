import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const mutation = `
  mutation metafieldDefinitionDelete($id: ID!) {
    metafieldDefinitionDelete(id: $id) {
      deletedMetafieldDefinitionId
      userErrors { field message }
    }
  }
  `;

  // ID da trovare per ricambi_associati
  const id_to_delete = "gid://shopify/MetafieldDefinition/417963114844"; // Verificare prima se è questo

  const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query: mutation, variables: { id: id_to_delete } }),
  });

  const result = await response.json();
  console.log("Risultato Eliminazione:", JSON.stringify(result, null, 2));
}

run().catch(console.error);
