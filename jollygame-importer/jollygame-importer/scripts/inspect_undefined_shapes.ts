import fs from "fs";
const data = JSON.parse(fs.readFileSync("final_pool_analysis.json", "utf-8"));
const undefinedShapes = data.filter((p: any) => p.forma === "Non definito");
console.log(`Totale forme non definite: ${undefinedShapes.length}`);
console.log("Esempi:");
console.log(undefinedShapes.slice(0, 10).map((p: any) => ({ title: p.title, brand: p.brand })));
