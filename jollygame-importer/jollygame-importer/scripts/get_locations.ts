import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function getLocations() {
  const query = `{
    locations(first: 5) {
      nodes {
        id
        name
        isPrimary
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
  console.log("Full response:", JSON.stringify(data, null, 2));
  if (data.data?.locations) {
    console.log(JSON.stringify(data.data.locations.nodes, null, 2));
  } else {
    console.error("Failed to fetch locations.");
  }
}

getLocations().catch(console.error);
