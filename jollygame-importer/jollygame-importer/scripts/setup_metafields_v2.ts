import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";

async function setupSchema() {
  const getMoQuery = `{ metaobjectDefinitions(first: 50) { nodes { id type } } }`;
  const listResult = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query: getMoQuery }),
  }).then(r => r.json());
  
  const moId = listResult.data?.metaobjectDefinitions?.nodes.find((n: any) => n.type === "documento_tecnico")?.id;

  if (!moId) {
    console.error("Metaobject definition 'documento_tecnico' not found.");
    return;
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
    validations: [{ name: "metaobject_definition_id", value: moId }]
  };

  const mfResult = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query: metafieldDefMutation, variables: { definition: metafieldDef } }),
  }).then(r => r.json());
  
  console.log("Metafield Def Result:", JSON.stringify(mfResult, null, 2));
}

setupSchema().catch(console.error);
