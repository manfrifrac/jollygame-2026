import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const mutation = `
  mutation metaobjectCreate($metaobject: MetaobjectCreateInput!) {
    metaobjectCreate(metaobject: $metaobject) {
      metaobject { id }
      userErrors { field message }
    }
  }
  `;

  const metaobject = {
    type: "ricambio",
    fields: [
      { key: "nome", value: "VITE 4*12 MM (*5)" },
      { key: "sku_originale", value: "R0516700" },
      { key: "prodotti_correlati", value: JSON.stringify(["gid://shopify/Product/15546247348572"]) }
    ]
  };

  const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query: mutation, variables: { metaobject } }),
  });

  const result = await response.json();
  console.log("Risultato:", JSON.stringify(result, null, 2));
}

run().catch(console.error);
