import dotenv from 'dotenv';
import fetch from 'node-fetch';
import fs from 'fs';

dotenv.config();

async function getLiveSkus() {
  const skus = new Set();
  let cursor = null;
  let hasNextPage = true;

  while (hasNextPage) {
    const query = `{
      products(first: 250, after: ${cursor ? `"${cursor}"` : "null"}, query: "status:active") {
        pageInfo { hasNextPage endCursor }
        nodes { variants(first: 10) { nodes { sku } } }
      }
    }`;
    const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json', 
        'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN 
      },
      body: JSON.stringify({ query }),
    });
    
    const result = await response.json();
    for (const p of result.data.products.nodes) {
      for (const v of p.variants.nodes) { if (v.sku) skus.add(v.sku); }
    }
    hasNextPage = result.data.products.pageInfo.hasNextPage;
    cursor = result.data.products.pageInfo.endCursor;
  }
  fs.writeFileSync('live_skus.json', JSON.stringify([...skus]));
  console.log("SKUs saved to live_skus.json");
}

getLiveSkus().catch(console.error);
