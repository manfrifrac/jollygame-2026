import fs from 'fs';
const products = JSON.parse(fs.readFileSync('shopify_all_products.json', 'utf8'));
products.forEach(p => console.log(`${p.vendor}: ${p.title} (${p.handle})`));
