import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";

async function setupSchema() {
  const metaobjectMutation = `
  mutation metaobjectDefinitionCreate($definition: MetaobjectDefinitionCreateInput!) {
    metaobjectDefinitionCreate(definition: $definition) {
      metaobjectDefinition {
        id
        type
      }
      userErrors {
        field
        message
      }
    }
  }
  `;

  const metaobjectDef = {
    name: "Documento Tecnico",
    type: "documento_tecnico",
    fieldDefinitions: [
      { name: "Titolo", key: "titolo", type: "single_line_text_field" },
      { name: "URL File", key: "url_file", type: "url" }
    ]
  };

  const moResult = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query: metaobjectMutation, variables: { definition: metaobjectDef } }),
  }).then(r => r.json());

  console.log("Metaobject Def Result:", JSON.stringify(moResult, null, 2));

  let moId = moResult.data?.metaobjectDefinitionCreate?.metaobjectDefinition?.id;
  
  // Se esiste già, recuperiamone l'ID
  if (!moId) {
      const getMoQuery = `{ metaobjectDefinitions(first: 50) { nodes { id type } } }`;
      const listResult = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
        body: JSON.stringify({ query: getMoQuery }),
      }).then(r => r.json());
      moId = listResult.data?.metaobjectDefinitions?.nodes.find((n: any) => n.type === "documento_tecnico")?.id;
  }

  const metafieldDefMutation = `
  mutation metafieldDefinitionCreate($definition: MetafieldDefinitionInput!) {
    metafieldDefinitionCreate(definition: $definition) {
      createdDefinition { id }
      userErrors { message }
    }
  }
  `;

  const metafieldDef = {
    name: "Documentazione Tecnica",
    namespace: "custom",
    key: "documentazione_tecnica",
    ownerType: "PRODUCT",
    type: "list.metaobject_reference",
    validationStatus: "ACTIVE",
    validations: [{ name: "metaobject_definition_id", value: moId }]
  };

  if (moId) {
    const mfResult = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
      body: JSON.stringify({ query: metafieldDefMutation, variables: { definition: metafieldDef } }),
    }).then(r => r.json());
    console.log("Metafield Def Result:", JSON.stringify(mfResult, null, 2));
  }
}

setupSchema().catch(console.error);
