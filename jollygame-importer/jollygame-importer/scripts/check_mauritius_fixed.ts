import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function checkGrePools() {
  const query = `{
    products(first: 250, query: "vendor:Gre") {
      nodes {
        id
        title
        status
        handle
        resourcePublications(first: 10) {
          nodes {
            isPublished
            publication { name }
          }
        }
      }
    }
  }`;

  const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!
    },
    body: JSON.stringify({ query })
  });

  const data = await res.json();
  const mauritius = data.data.products.nodes.filter((p: any) => p.title.includes("Mauritius"));
  console.log(JSON.stringify(mauritius, null, 2));
}

checkGrePools().catch(console.error);
