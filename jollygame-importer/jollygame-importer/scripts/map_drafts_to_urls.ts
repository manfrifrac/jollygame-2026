import fs from "fs";
import { parse } from "csv-parse/sync";

const drafts = JSON.parse(fs.readFileSync("gre_drafts_to_scrape.json", "utf8"));
const alignmentReport = fs.readFileSync("../../gre_alignment_final_report.csv", "utf8");
const records = parse(alignmentReport, { columns: true, skip_empty_lines: true });

const mapped = drafts.map(d => {
    const match = records.find(r => r.SKU === d.sku);
    return {
        ...d,
        gre_url: match ? match.Grepool_URL : null
    };
});

fs.writeFileSync("gre_mapped_drafts.json", JSON.stringify(mapped, null, 2));

const missingUrl = mapped.filter(m => !m.gre_url).length;
console.log(`📊 Mappatura completata.`);
console.log(`✅ URL trovati: ${mapped.length - missingUrl}`);
console.log(`⚠️ URL mancanti: ${missingUrl}`);

if (missingUrl > 0) {
    console.log("\nEsempi senza URL:");
    mapped.filter(m => !m.gre_url).slice(0, 5).forEach(m => console.log(` - ${m.title} (SKU: ${m.sku})`));
}
