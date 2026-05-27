import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function checkMauritius() {
  const query = `{
    products(first: 20, query: "title:Mauritius") {
      nodes {
        id
        title
        status
        handle
        onlineStoreUrl
        resourcePublications(first: 10) {
          nodes {
            isPublished
            publication {
              name
            }
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
  console.log(JSON.stringify(data.data.products.nodes, null, 2));
}

checkMauritius().catch(console.error);
