import fs from "fs";
const data = JSON.parse(fs.readFileSync("catalog_visibility_report.json", "utf-8"));
const zeroPrice = data.details.filter((p: any) => p.price === 0);
console.log(`Totale prodotti a zero: ${zeroPrice.length}`);
console.log("Esempi di titoli a zero:");
console.log(zeroPrice.slice(0, 50).map((p: any) => p.title));
