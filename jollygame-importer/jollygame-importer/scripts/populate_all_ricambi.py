import sqlite3, json, fetch from 'node-fetch';
import dotenv from 'dotenv';
dotenv.config();

// Script per associare massivamente i Ricambi ai Prodotti
async function run() {
  const shop_products = JSON.parse(require('fs').readFileSync('jollygame-importer/jollygame-importer/shopify_products.json', 'utf8'));
  const sku_to_id = { p.sku: p.id for p in shop_products if p.sku };

  const conn = sqlite3.connect('fluidra_catalog.db');
  const cursor = conn.cursor();
  // Estraiamo tutti i ricambi per ogni piscina
  cursor.execute('SELECT r.parent_sku, r.child_sku, p.title FROM product_relations r JOIN products p ON r.child_sku = p.sku');
  const rows = cursor.fetchall();

  // Organizziamo per piscina
  const mapping = {};
  for (const (p_sku, c_sku, c_title) in rows) {
    if (sku_to_id[p_sku]) {
      mapping.setdefault(sku_to_id[p_sku], []).append({sku: c_sku, title: c_title});
    }
  }

  // Ora per ogni piscina, creiamo i metaobject Ricambio e aggiorniamo il prodotto
  // (Omettiamo la creazione massiva qui per brevità, mostro la logica)
}
run();
