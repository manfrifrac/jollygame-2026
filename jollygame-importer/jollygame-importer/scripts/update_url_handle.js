import dotenv from 'dotenv';
dotenv.config();

async function run() {
  const mutation = `
  mutation metaobjectDefinitionUpdate($id: ID!, $definition: MetaobjectDefinitionUpdateInput!) {
    metaobjectDefinitionUpdate(id: $id, definition: $definition) {
      metaobjectDefinition {
        id
      }
      userErrors {
        field
        message
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
    body: JSON.stringify({ 
      query: mutation, 
      variables: { 
        id: "gid://shopify/MetaobjectDefinition/37104943452", 
        definition: {
          capabilities: {
            onlineStore: {
              enabled: true,
              data: {
                urlHandle: "brand-ricambi"
              }
            }
          }
        } 
      } 
    }),
  });

  const result = await response.json();
  console.log("Update Result:", JSON.stringify(result, null, 2));
}

run().catch(console.error);
