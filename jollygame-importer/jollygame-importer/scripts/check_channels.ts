import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";

const query = `
{
  publications(first: 20) {
    nodes {
      id
      name
    }
  }
}
`;

async function checkChannels() {
  const response = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN,
    },
    body: JSON.stringify({ query }),
  });

  const result: any = await response.json();
  console.log(JSON.stringify(result.data.publications.nodes, null, 2));
}

checkChannels().catch(console.error);
