import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function draftZeroPriceProducts() {
  console.log("🛡️ Protezione Store: Spostamento prodotti con prezzo 0 in BOZZA...");

  let hasNextPage = true;
  let cursor = null;
  let count = 0;

  while (hasNextPage) {
    const query = `
    query getZeroPrice($cursor: String) {
      products(first: 250, after: $cursor, query: "status:active") {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          variants(first: 5) {
            nodes {
              price
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
      const hasZeroPrice = product.variants.nodes.some((v: any) => parseFloat(v.price) <= 0);
      
      if (hasZeroPrice) {
        console.log(`📝 Spostando in Bozza: ${product.title}`);
        
        const mutation = `
        mutation productUpdate($input: ProductInput!) {
          productUpdate(input: $input) {
            product { id status }
            userErrors { message }
          }
        }
        `;

        const updateRes = await shopifyRequest(mutation, {
          input: {
            id: product.id,
            status: "DRAFT"
          }
        });

        if (updateRes.data?.productUpdate?.userErrors?.length > 0) {
            console.error(`❌ Errore per ${product.title}:`, updateRes.data.productUpdate.userErrors);
        } else {
            count++;
        }
      }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`\n✅ Operazione completata. ${count} prodotti spostati in Bozza.`);
}

draftZeroPriceProducts().catch(console.error);
