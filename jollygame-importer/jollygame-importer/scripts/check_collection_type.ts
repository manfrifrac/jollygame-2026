import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function checkCollectionType() {
  const query = `{
    collections(first: 20) {
      nodes {
        id
        title
        handle
        ruleSet {
          rules {
            column
            relation
            condition
          }
        }
      }
    }
  }`;
  const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query }),
  });
  const data = await res.json();
  console.log(JSON.stringify(data.data.collections.nodes, null, 2));
}

checkCollectionType().catch(console.error);
