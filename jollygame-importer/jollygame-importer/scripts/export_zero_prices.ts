import fs from "fs";
import path from "path";

async function exportZeroPriceCsv() {
    console.log("📄 Generazione CSV prodotti con prezzo mancante...");
    
    const reportPath = path.resolve("catalog_visibility_report.json");
    if (!fs.existsSync(reportPath)) return;

    const data = JSON.parse(fs.readFileSync(reportPath, "utf-8"));
    const zeroPrice = data.details.filter((p: any) => p.price === 0);

    let csv = "Titolo,Handle,SKU Attuale,Prezzo da Inserire\n";
    for (const p of zeroPrice) {
        csv += `"${p.title.replace(/"/g, '""')}","${p.handle}","${p.sku || ''}",\n`;
    }

    fs.writeFileSync("prodotti_prezzo_zero.csv", csv);
    console.log(`✅ Creato file 'prodotti_prezzo_zero.csv' con ${zeroPrice.length} righe.`);
}

exportZeroPriceCsv().catch(console.error);
