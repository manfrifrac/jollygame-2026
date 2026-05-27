import sqlite3, json, fetch from 'node-fetch';
import dotenv from 'dotenv';
dotenv.config();

// Configurazione
const SHOPIFY_API_URL = `https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`;
const HEADERS = {
  'Content-Type': 'application/json',
  'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN
};

async function shopifyQuery(query, variables = {}) {
  const response = await fetch(SHOPIFY_API_URL, {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify({ query, variables }),
  });
  return response.json();
}

async function run() {
  // 1. Carica mapping
  const shop_products = JSON.parse(require('fs').readFileSync('jollygame-importer/jollygame-importer/shopify_products.json', 'utf8'));
  const sku_to_id = {};
  for (const p of shop_products) {
    if (p.sku) sku_to_id[p.sku] = p.id;
  }

  // 2. Connetti DB
  const conn = sqlite3.connect('fluidra_catalog.db');
  const cursor = conn.cursor();
  cursor.execute('SELECT parent_sku, child_sku, title FROM products JOIN product_relations ON sku=child_sku');
  const rows = cursor.fetchall();

  // 3. Mappa ricambi per piscina
  const mapping = {};
  for (const (p_sku, c_sku, c_title) in rows) {
    // Tenta un match grezzo: se il parent_sku è parte dello SKU shopify
    for (const shop_sku in sku_to_id) {
        if (p_sku in shop_sku || shop_sku in p_sku) {
            mapping.setdefault(sku_to_id[shop_sku], []).append({sku: c_sku, title: c_title});
            break;
        }
    }
  }

  // 4. Per ogni piscina, crea i ricambi e aggiorna il prodotto
  for (const (product_id, ricambi) in mapping.items()) {
     // Crea i metaobject, raccogli gli ID e poi aggiorna il metafield del prodotto
  }
}
