import fs from "fs";
const data = JSON.parse(fs.readFileSync("catalog_visibility_report.json", "utf-8"));

// Prodotti di punta da filtrare
const targetKeywords = ["iq", "exo", "ei", "inverter", "pool", "piscina"];
const priorityProducts = data.details.filter((p: any) => 
    p.price === 0 && 
    targetKeywords.some(k => p.title.toLowerCase().includes(k))
);

console.log(`🔍 Trovati ${priorityProducts.length} prodotti di punta a prezzo zero:`);
priorityProducts.forEach((p: any) => console.log(`- ${p.title} (SKU: ${p.sku})`));
fs.writeFileSync("priority_audit_list.json", JSON.stringify(priorityProducts, null, 2));
