import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const mutation = `
  mutation CreateMetafieldDefinition($definition: MetafieldDefinitionInput!) {
    metafieldDefinitionCreate(definition: $definition) {
      createdDefinition { id }
      userErrors { field message }
    }
  }
  `;

  const definition = {
    name: "Ricambi Associati",
    namespace: "custom",
    key: "ricambi_associati",
    type: "list.metaobject_reference",
    ownerType: "PRODUCT",
    validations: [{ name: "metaobject_definition_id", value: "gid://shopify/MetaobjectDefinition/37148787036" }]
  };

  const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query: mutation, variables: { definition } }),
  });

  const result = await response.json();
  console.log("Risultato:", JSON.stringify(result, null, 2));
}

run().catch(console.error);
