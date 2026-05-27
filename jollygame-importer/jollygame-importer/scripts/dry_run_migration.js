import dotenv from 'dotenv';
import fetch from 'node-fetch';
import sqlite3 from 'sqlite3';

dotenv.config();

async function getLiveProducts() {
  const map = new Map(); // SKU -> product_id
  let cursor = null;
  let hasNextPage = true;

  console.log("Fetching live product IDs...");

  while (hasNextPage) {
    const query = `{
      products(first: 250, after: ${cursor ? `"${cursor}"` : "null"}, query: "status:active") {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
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
        if (v.sku) map.set(v.sku, p.id);
      }
    }
    
    hasNextPage = pageInfo.hasNextPage;
    cursor = pageInfo.endCursor;
  }
  return map;
}

async function run() {
  const liveProducts = await getLiveProducts();
  const db = new sqlite3.Database('fluidra_catalog.db');
  
  db.all("SELECT parent_sku, child_sku FROM product_relations", [], (err, rows) => {
    if (err) throw err;
    
    let matches = 0;
    const report = [];

    for (const row of rows) {
      if (liveProducts.has(row.parent_sku)) {
        matches++;
        if (matches <= 10) {
          report.push({
            parentSku: row.parent_sku,
            childSku: row.child_sku,
            shopifyId: liveProducts.get(row.parent_sku)
          });
        }
      }
    }
    
    console.log(`Dry-run complete. Potential Ricambi to migrate: ${matches}`);
    console.log("Sample mappings:", JSON.stringify(report, null, 2));
    db.close();
  });
}

run().catch(console.error);
