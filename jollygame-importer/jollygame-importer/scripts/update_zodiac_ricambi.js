import dotenv from 'dotenv';
dotenv.config();

async function run() {
  const query = `{
    products(first: 50, query: "vendor:Zodiac") {
      nodes {
        id
        title
        productType
        vendor
        tags
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
  const zodiacProducts = result.data.products.nodes;
  
  // Aggiorniamo alcuni prodotti Zodiac per farli apparire come ricambi
  // In uno scenario reale andrebbero identificati tramite keyword o logica,
  // qui li forziamo per testare la visualizzazione.
  const toUpdate = zodiacProducts.slice(0, 5); 

  console.log(`Updating ${toUpdate.length} Zodiac products to 'Ricambio' type...`);

  const mutation = `
  mutation productUpdate($input: ProductInput!) {
    productUpdate(input: $input) {
      product {
        id
        title
      }
      userErrors {
        field
        message
      }
    }
  }
  `;

  for (const p of toUpdate) {
    const input = {
      id: p.id,
      productType: "Ricambio",
      tags: [...new Set([...(p.tags || []), "Tipo: Ricambio"])]
    };

    const updateResponse = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
      },
      body: JSON.stringify({ query: mutation, variables: { input } }),
    });

    const updateResult = await updateResponse.json();
    if (updateResult.data?.productUpdate?.userErrors.length > 0) {
      console.error(`Error updating ${p.title}:`, updateResult.data.productUpdate.userErrors);
    } else {
      console.log(`Updated: ${p.title}`);
    }
  }
}

run().catch(console.error);
