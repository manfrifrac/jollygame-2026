import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function testConsolidateOne() {
  const masterId = "gid://shopify/Product/15597334692188"; // KITPROV7388N
  const otherId = "gid://shopify/Product/15598146847068";  // Duplicate? No, let's find a different size.
  
  // Let's just try to update the master first.
  const mutation = `
  mutation productUpdate($input: ProductInput!) {
    productUpdate(input: $input) {
      product { id title options { name values } }
      userErrors { field message }
    }
  }
  `;

  const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!
    },
    body: JSON.stringify({
      query: mutation,
      variables: {
        input: {
          id: masterId,
          title: "Piscina Gre Serie Islanda (Nordic Omega TEST)"
        }
      }
    })
  });

  const data = await res.json();
  console.log(JSON.stringify(data, null, 2));
}

testConsolidateOne().catch(console.error);
