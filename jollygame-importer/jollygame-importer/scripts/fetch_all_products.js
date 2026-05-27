import dotenv from 'dotenv';
import fs from 'fs';
dotenv.config();

async function run() {
  let allProducts = [];
  let hasNextPage = true;
  let cursor = null;

  while (hasNextPage) {
    const query = `
    query getProducts($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          title
          handle
          vendor
          tags
          variants(first: 10) {
            nodes {
              sku
            }
          }
        }
      }
    }
    `;

    const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
      },
      body: JSON.stringify({ query, variables: { cursor } }),
    });

    const result = await response.json();
    if (result.errors) {
      console.error(result.errors);
      break;
    }

    const products = result.data.products.nodes;
    allProducts.push(...products);

    hasNextPage = result.data.products.pageInfo.hasNextPage;
    cursor = result.data.products.pageInfo.endCursor;
    console.log(`Fetched ${allProducts.length} products...`);
  }

  fs.writeFileSync('shopify_all_products.json', JSON.stringify(allProducts, null, 2));
  console.log('Saved to shopify_all_products.json');
}

run().catch(console.error);
