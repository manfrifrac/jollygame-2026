import dotenv from 'dotenv';
import fetch from 'node-fetch';
import fs from 'fs';

dotenv.config();

async function exportProducts() {
  const products = [];
  let cursor = null;
  let hasNextPage = true;

  while (hasNextPage) {
    const query = `{
      products(first: 250, after: ${cursor ? `"${cursor}"` : "null"}, query: "status:active") {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          variants(first: 1) { nodes { sku } }
        }
      }
    }`;
    const res = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN },
      body: JSON.stringify({ query }),
    }).then(r => r.json());
    
    for (const p of res.data.products.nodes) {
      const sku = p.variants.nodes[0]?.sku;
      products.push({ id: p.id, title: p.title, sku: sku });
    }
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }
  fs.writeFileSync('shopify_products.json', JSON.stringify(products));
}

exportProducts().catch(console.error);
