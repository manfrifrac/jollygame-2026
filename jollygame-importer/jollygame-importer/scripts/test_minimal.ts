import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";

const mutation = `
mutation productCreate($input: ProductInput!) {
  productCreate(input: $input) {
    product {
      id
      title
    }
    userErrors {
      field
      message
    }
  }
}
`;

async function testMinimalProduct() {
  const input = {
    title: "Test Product Minimal",
    vendor: "Zodiac",
    status: "DRAFT"
  };

  const response = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN,
    },
    body: JSON.stringify({
      query: mutation,
      variables: { input },
    }),
  });

  const result: any = await response.json();
  console.log(JSON.stringify(result, null, 2));
}

testMinimalProduct().catch(console.error);
