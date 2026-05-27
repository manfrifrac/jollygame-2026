import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";

const mutation = `
mutation metafieldDefinitionCreate($definition: MetafieldDefinitionInput!) {
  metafieldDefinitionCreate(definition: $definition) {
    createdDefinition {
      id
      name
    }
    userErrors {
      field
      message
    }
  }
}
`;

async function createDefinitions() {
  const definitions = [
    {
      name: "Manuali e Documenti PDF",
      namespace: "custom",
      key: "manuali_pdf",
      ownerType: "PRODUCT",
      type: "json"
    },
    {
      name: "Video YouTube",
      namespace: "custom",
      key: "video_youtube",
      ownerType: "PRODUCT",
      type: "list.single_line_text_field"
    }
  ];

  for (const definition of definitions) {
    const response = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN!,
      },
      body: JSON.stringify({
        query: mutation,
        variables: { definition },
      }),
    });

    const result: any = await response.json();
    if (result.data?.metafieldDefinitionCreate?.userErrors?.length > 0) {
      console.log(`Info per ${definition.key}:`, result.data.metafieldDefinitionCreate.userErrors[0].message);
    } else {
      console.log(`Successo per ${definition.key}:`, result.data?.metafieldDefinitionCreate?.createdDefinition?.id);
    }
  }
}

createDefinitions().catch(console.error);
