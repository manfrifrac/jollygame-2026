import dotenv from 'dotenv';
dotenv.config();

async function run() {
  const metaobjectMutation = `
  mutation metaobjectDefinitionCreate($definition: MetaobjectDefinitionCreateInput!) {
    metaobjectDefinitionCreate(definition: $definition) {
      metaobjectDefinition {
        id
        type
        name
      }
      userErrors {
        field
        message
      }
    }
  }
  `;

  const metaobjectDef = {
    name: "Brand Ricambi",
    type: "brand_ricambi",
    capabilities: {
      publishable: {
        enabled: true
      }
    },
    fieldDefinitions: [
      { name: "Nome", key: "nome", type: "single_line_text_field" },
      { name: "Logo", key: "logo", type: "file_reference" },
      { name: "Descrizione", key: "descrizione", type: "rich_text_field" },
      { name: "SEO Title", key: "seo_title", type: "single_line_text_field" },
      { name: "SEO Description", key: "seo_description", type: "single_line_text_field" }
    ]
  };

  const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query: metaobjectMutation, variables: { definition: metaobjectDef } }),
  });

  const result = await response.json();
  console.log("Result:", JSON.stringify(result, null, 2));
}

run().catch(console.error);
