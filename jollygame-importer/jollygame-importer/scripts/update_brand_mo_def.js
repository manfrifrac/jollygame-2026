import dotenv from 'dotenv';
import fetch from 'node-fetch';

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

  const defId = "gid://shopify/MetaobjectDefinition/37104943452"; // brand_ricambi

  const updateResponse = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN },
    body: JSON.stringify({ 
      query: mutation, 
      variables: { 
        id: defId,
        definition: {
          fieldDefinitions: [
            {
              create: {
                name: "Ricambi Associati",
                key: "ricambi_associati",
                type: "list.metaobject_reference",
                validations: [{ name: "metaobject_definition_id", value: "gid://shopify/MetaobjectDefinition/37148787036" }]
              }
            }
          ]
        }
      } 
    }),
  });

  const updateResult = await updateResponse.json();
  console.log("Result:", JSON.stringify(updateResult, null, 2));
}

run().catch(console.error);
