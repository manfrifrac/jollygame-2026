import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const mutation = `
  mutation metaobjectDefinitionUpdate($id: ID!, $definition: MetaobjectDefinitionUpdateInput!) {
    metaobjectDefinitionUpdate(id: $id, definition: $definition) {
      metaobjectDefinition {
        id
        capabilities {
          onlineStore { enabled }
        }
      }
      userErrors { field message }
    }
  }
  `;

  // Aggiorniamo per abilitare esplicitamente l'accesso Storefront
  const definition = {
    capabilities: {
      onlineStore: { 
        enabled: true,
        data: { urlHandle: "nome" }
      }
    }
  };

  const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ 
      query: mutation, 
      variables: { 
        id: "gid://shopify/MetaobjectDefinition/37148787036", 
        definition 
      } 
    }),
  });

  const result = await response.json();
  console.log("Risultato Update:", JSON.stringify(result, null, 2));
}

run().catch(console.error);
