import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const productId = "gid://shopify/Product/15527758365020";
  const query = `{
    product(id: "${productId}") {
      id
      title
    }
  }`;

  const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query }),
  });

  const result = await response.json();
  if (result.data.product) {
      console.log(`Titolo attuale (2): ${result.data.product.title}`);
  } else {
      console.log("Prodotto non trovato.");
  }
}

run().catch(console.error);
