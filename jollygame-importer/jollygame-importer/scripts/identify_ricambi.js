import dotenv from 'dotenv';
dotenv.config();

async function run() {
  let allProducts = [];
  let cursor = null;
  let hasNextPage = true;

  console.log("Fetching all products to identify Ricambi...");

  while (hasNextPage) {
    const query = `{
      products(first: 250, after: ${cursor ? `"${cursor}"` : "null"}) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          title
          productType
          vendor
          variants(first: 1) {
            nodes {
              sku
              barcode
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
    if (result.errors) {
      console.error(result.errors);
      break;
    }

    const { nodes, pageInfo } = result.data.products;
    allProducts.push(...nodes);
    hasNextPage = pageInfo.hasNextPage;
    cursor = pageInfo.endCursor;
  }

  const ricambi = allProducts.filter(p => 
    p.title.toLowerCase().includes("ricambio") || 
    p.title.toLowerCase().includes("parti di") ||
    p.productType.toLowerCase().includes("ricambio") ||
    p.productType.toLowerCase().includes("accessori")
  );

  console.log(`Found ${ricambi.length} potential Ricambi.`);
  
  for (const p of ricambi) {
    console.log(`- ${p.title} (${p.vendor})`);
  }
}

run().catch(console.error);
