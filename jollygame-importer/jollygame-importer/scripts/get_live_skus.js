import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function getLiveProductSkus() {
  const skus = new Set();
  let cursor = null;
  let hasNextPage = true;

  console.log("Fetching live product SKUs...");

  while (hasNextPage) {
    const query = `{
      products(first: 250, after: ${cursor ? `"${cursor}"` : "null"}, query: "status:active") {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          variants(first: 10) {
            nodes {
              sku
            }
          }
        }
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
    const { nodes, pageInfo } = result.data.products;
    
    for (const p of nodes) {
      for (const v of p.variants.nodes) {
        if (v.sku) skus.add(v.sku);
      }
    }
    
    hasNextPage = pageInfo.hasNextPage;
    cursor = pageInfo.endCursor;
  }
  
  return skus;
}

getLiveProductSkus().then(skus => {
  console.log(`Found ${skus.size} live product SKUs.`);
  // Stampa un campione per verifica
  console.log("Sample:", [...skus].slice(0, 5));
});
