import sqlite3, json, fetch from 'node-fetch';
import dotenv from 'dotenv';
dotenv.config();

async function run() {
  const db = new sqlite3.Database('fluidra_catalog.db');
  
  // Usiamo WR000500 come piscina di test
  const parent_sku = 'WR000500';
  const shopify_product_id = 'gid://shopify/Product/15527758365020'; // ID corretto per CNX 50 iQ

  db.get('SELECT p.sku, p.title FROM products p JOIN product_relations r ON p.sku = r.child_sku WHERE r.parent_sku = ? LIMIT 1', [parent_sku], async (err, part) => {
    if (err || !part) {
      console.log("Nessun ricambio trovato");
      db.close();
      return;
    }

    const { sku: part_sku, title: part_title } = part;
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
    db.close();
  });
}

run().catch(console.error);
