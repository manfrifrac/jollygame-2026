import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const productId = "gid://shopify/Product/15546248167772";
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
  const product = result.data.product;
  console.log(`Titolo attuale: ${product.title}`);

  if (product.title.includes('1~')) {
    const newTitle = product.title.replace('1~', '').trim();
    console.log(`Correzione titolo in: ${newTitle}`);

    const mutation = `
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product { id title }
      }
    }
    `;

    await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
      },
      body: JSON.stringify({ query: mutation, variables: { input: { id: productId, title: newTitle } } }),
    });
    console.log("Titolo corretto.");
  }
}

run().catch(console.error);
