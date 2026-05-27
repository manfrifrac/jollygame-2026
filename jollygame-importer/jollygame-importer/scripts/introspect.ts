import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";

const query = `
{
  __type(name: "ProductInput") {
    inputFields {
      name
      type {
        name
        kind
        ofType {
          name
          kind
        }
      }
    }
  }
}
`;

async function introspectProductInput() {
  const response = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN,
    },
    body: JSON.stringify({ query }),
  });

  const result: any = await response.json();
  console.log(JSON.stringify(result.data.__type.inputFields.map((f: any) => f.name), null, 2));
}

introspectProductInput().catch(console.error);
