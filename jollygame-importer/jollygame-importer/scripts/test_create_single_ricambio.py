import dotenv from 'dotenv';
import fetch from 'node-fetch';
import sqlite3 from 'sqlite3';

dotenv.config();

async function run() {
  const conn = sqlite3.connect('fluidra_catalog.db');
  const cursor = conn.cursor();
  
  // SKU della piscina: 1233741
  // ID Shopify Piscina: gid://shopify/Product/15546247348572
  const parent_sku = '1233741';
  const shopify_product_id = 'gid://shopify/Product/15546247348572';

  // Prendo il primo ricambio disponibile
  cursor.execute('SELECT p.sku, p.title FROM products p JOIN product_relations r ON p.sku = r.child_sku WHERE r.parent_sku = ? LIMIT 1', (parent_sku,))
  const part = cursor.fetchone();
  conn.close();

  if (!part) {
    console.log("Nessun ricambio trovato per questo SKU");
    return;
  }

  const [part_sku, part_title] = part;
  console.log(`Creazione ricambio: ${part_title} (${part_sku}) per piscina ${parent_sku}`);

  const mutation = `
  mutation metaobjectCreate($metaobject: MetaobjectCreateInput!) {
    metaobjectCreate(metaobject: $metaobject) {
      metaobject { id handle }
      userErrors { field message }
    }
  }
  `;

  const metaobject = {
    type: "ricambio",
    fields: [
      { key: "nome", value: part_title },
      { key: "sku_originale", value: part_sku },
      { key: "prodotti_correlati", value: JSON.stringify([shopify_product_id]) }
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
