import fs from "fs";
const data = JSON.parse(fs.readFileSync("catalog_visibility_report.json", "utf-8"));
const withPrice = data.details.filter((p: any) => p.price > 0);
console.log(`Prodotti con prezzo > 0: ${withPrice.length}`);
