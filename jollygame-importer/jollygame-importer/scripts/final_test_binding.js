import dotenv from 'dotenv';
import fetch from 'node-fetch';
import sqlite3 from 'sqlite3';

dotenv.config();

async function run() {
  const db = new sqlite3.Database('C:/Users/Riccardo/Desktop/Manfredo/JollyGame/fluidra_catalog.db');
  
  const parent_sku = 'WR000500';
  const product_id = 'gid://shopify/Product/15527758365020';

  // 1. Prendi un ricambio dal DB
  db.get('SELECT p.sku, p.title FROM products p JOIN product_relations r ON p.sku = r.child_sku WHERE r.parent_sku = ? LIMIT 1', [parent_sku], async (err, part) => {
    if (err || !part) {
      console.log("Nessun ricambio trovato");
      db.close();
      return;
    }

    const { sku: part_sku, title: part_title } = part;
    console.log(`Test: Creazione metaobject per ${part_title} (${part_sku})`);

    // 2. Creazione Metaobject
    const mutationCreate = `
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
        { key: "nome", value: part_title },
        { key: "sku_originale", value: part_sku }
      ]
    };

    const responseCreate = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN },
      body: JSON.stringify({ query: mutationCreate, variables: { metaobject } }),
    });

    const resCreate = await responseCreate.json();
    const ricambio_id = resCreate.data.metaobjectCreate.metaobject.id;
    console.log(`Metaobject creato: ${ricambio_id}`);

    // 3. Associazione al prodotto (aggiornamento metafield)
    const mutationUpdate = `
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product { id }
        userErrors { field message }
      }
    }
    `;

    const input = {
      id: product_id,
      metafields: [
        {
          namespace: "custom",
          key: "ricambi_compatibili",
          type: "list.metaobject_reference",
          value: JSON.stringify([ricambio_id])
        }
      ]
    };

    const responseUpdate = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN },
      body: JSON.stringify({ query: mutationUpdate, variables: { input } }),
    });

    const resUpdate = await responseUpdate.json();
    console.log("Risultato associazione:", JSON.stringify(resUpdate, null, 2));
    db.close();
  });
}

run().catch(console.error);
