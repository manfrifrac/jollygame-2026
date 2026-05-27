import fs from 'fs';
import dotenv from 'dotenv';
import fetch from 'node-fetch';
import path from 'path';

const envPath = '.env';
const envConfig = dotenv.parse(fs.readFileSync(envPath));

async function getAllShopifyProducts() {
  let allProducts = [];
  let hasNextPage = true;
  let cursor = null;

  while (hasNextPage) {
    const query = `
      query ($cursor: String) {
        products(first: 250, after: $cursor) {
          pageInfo {
            hasNextPage
            endCursor
          }
          edges {
            node {
              id
              title
              handle
              vendor
              variants(first: 10) {
                edges {
                  node {
                    sku
                  }
                }
              }
            }
          }
        }
      }
    `;

    const response = await fetch(`https://${envConfig.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': envConfig.SHOPIFY_ACCESS_TOKEN
      },
      body: JSON.stringify({ query, variables: { cursor } })
    });

    const data = await response.json();
    if (data.errors) {
      console.error(JSON.stringify(data.errors, null, 2));
      break;
    }

    const products = data.data.products.edges.map(e => ({
      id: e.node.id,
      title: e.node.title,
      handle: e.node.handle,
      vendor: e.node.vendor,
      skus: e.node.variants.edges.map(v => v.node.sku).filter(s => s)
    }));

    allProducts.push(...products);
    hasNextPage = data.data.products.pageInfo.hasNextPage;
    cursor = data.data.products.pageInfo.endCursor;
  }

  return allProducts;
}

function getJsonProducts(fileName) {
  const filePath = path.join('..', '..', fileName);
  if (!fs.existsSync(filePath)) return [];
  const content = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  const products = [];
  
  if (Array.isArray(content)) {
    content.forEach(item => {
      if (item.sku) products.push(item.sku.trim().toUpperCase());
    });
  } else {
    for (const category in content) {
      content[category].forEach(item => {
        if (item.sku) products.push(item.sku.trim().toUpperCase());
      });
    }
  }
  return Array.from(new Set(products));
}

async function compare() {
  console.log('Fetching all Shopify products...');
  const allShopifyProducts = await getAllShopifyProducts();
  const shopifySkus = new Map(); // SKU -> {title, vendor}
  
  allShopifyProducts.forEach(p => {
    p.skus.forEach(sku => {
      shopifySkus.set(sku.trim().toUpperCase(), { title: p.title, vendor: p.vendor });
    });
  });

  const familyPlanSkus = getJsonProducts('gre_family_import_plan.json');
  const newImportSkus = getJsonProducts('new_gre_products_to_import.json');
  const kitsOnlyPlanSkus = getJsonProducts('gre_kits_only_plan.json');

  const allLocalSkus = new Set([...familyPlanSkus, ...newImportSkus, ...kitsOnlyPlanSkus]);

  console.log(`\nShopify Statistics:`);
  console.log(`Total Products: ${allShopifyProducts.length}`);
  console.log(`Unique SKUs: ${shopifySkus.size}`);
  console.log(`Gre Vendor Products: ${allShopifyProducts.filter(p => p.vendor === 'Gre').length}`);

  console.log(`\nLocal Files Statistics:`);
  console.log(`gre_family_import_plan.json: ${familyPlanSkus.length} unique SKUs`);
  console.log(`new_gre_products_to_import.json: ${newImportSkus.length} unique SKUs`);
  console.log(`gre_kits_only_plan.json: ${kitsOnlyPlanSkus.length} unique SKUs`);
  console.log(`Total unique SKUs in local files: ${allLocalSkus.size}`);

  const missing = [];
  allLocalSkus.forEach(sku => {
    if (!shopifySkus.has(sku)) {
      missing.push(sku);
    }
  });

  console.log(`\n--- Missing on Shopify (${missing.length}) ---`);
  missing.forEach(sku => {
    let source = [];
    if (familyPlanSkus.includes(sku)) source.push('family_plan');
    if (newImportSkus.includes(sku)) source.push('new_import');
    if (kitsOnlyPlanSkus.includes(sku)) source.push('kits_only');
    console.log(`${sku} [${source.join(', ')}]`);
  });

  const extra = [];
  shopifySkus.forEach((val, sku) => {
    if (!allLocalSkus.has(sku) && val.vendor === 'Gre') {
      extra.push({ sku, ...val });
    }
  });

  console.log(`\n--- Extra on Shopify (${extra.length}) (Vendor: Gre, not in local lists) ---`);
  extra.slice(0, 20).forEach(p => console.log(`${p.sku}: ${p.title}`));
  if (extra.length > 20) console.log('...');

  // Check if some "missing" are actually there but with different SKUs (maybe partial match?)
  // For now just exact SKU match.
}

compare();
