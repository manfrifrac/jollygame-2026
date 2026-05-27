import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const mutation = `
  mutation metaobjectDefinitionCreate($definition: MetaobjectDefinitionCreateInput!) {
    metaobjectDefinitionCreate(definition: $definition) {
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

  const metaobjectDef = {
    name: "Ricambio",
    type: "ricambio",
    capabilities: {
      publishable: { enabled: true },
      onlineStore: { 
        enabled: true,
        data: { urlHandle: "nome" }
      }
    },
    fieldDefinitions: [
      { name: "Nome", key: "nome", type: "single_line_text_field" },
      { name: "SKU Originale", key: "sku_originale", type: "single_line_text_field" },
      { name: "Categoria Tecnica", key: "categoria_tecnica", type: "single_line_text_field" },
      { name: "Materiale", key: "materiale", type: "single_line_text_field" },
      { name: "Prodotti Correlati", key: "prodotti_correlati", type: "list.product_reference" },
      { name: "Note Compatibilità", key: "note_compatibilita", type: "multi_line_text_field" }
    ]
  };

  const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query: mutation, variables: { definition: metaobjectDef } }),
  });

  const result = await response.json();
  console.log("Result:", JSON.stringify(result, null, 2));
}

run().catch(console.error);
