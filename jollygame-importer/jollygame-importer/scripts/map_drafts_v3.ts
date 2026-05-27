import fs from "fs";
import { parse } from "csv-parse/sync";

const drafts = JSON.parse(fs.readFileSync("gre_drafts_to_scrape.json", "utf8"));

// Files to check for URLs
const mappingFiles = [
    "mapping_prodotti_jolly_gre_FINALE.csv",
    "gre_alignment_final_report.csv",
    "REPORT_REVISIONE_JOLLYGAME_2026.csv"
];

const allRecords: any[] = [];

for (const file of mappingFiles) {
    if (fs.existsSync("../../" + file)) {
        const content = fs.readFileSync("../../" + file, "utf8");
        // Try to detect separator
        const delimiter = content.includes(";") ? ";" : ",";
        try {
            const records = parse(content, { 
                columns: true, 
                skip_empty_lines: true,
                delimiter: delimiter,
                relax_column_count: true
            });
            allRecords.push(...records);
        } catch (e) {
            console.error(`Error parsing ${file}: ${e.message}`);
        }
    }
}

console.log(`Loaded ${allRecords.length} records from mapping files.`);

const mapped = drafts.map(d => {
    let url = null;
    let matchMethod = "none";

    // 1. Match by SKU (exact)
    if (d.sku) {
        const match = allRecords.find(r => 
            (r.SKU && r.SKU.trim().toUpperCase() === d.sku.trim().toUpperCase()) ||
            (r.sku && r.sku.trim().toUpperCase() === d.sku.trim().toUpperCase())
        );
        if (match) {
            url = match.Grepool_URL || match.url || match.URL_Grepool || match.Gre_Popup_URL;
            if (url) matchMethod = "SKU exact";
        }
    }

    // 2. Match by Title (partial)
    if (!url) {
        const match = allRecords.find(r => {
            const rTitle = (r.Titolo || r.title || r.Title || "").toLowerCase();
            const dTitle = d.title.toLowerCase();
            return rTitle && (rTitle.includes(dTitle) || dTitle.includes(rTitle));
        });
        if (match) {
            url = match.Grepool_URL || match.url || match.URL_Grepool || match.Gre_Popup_URL;
            if (url) matchMethod = "Title match";
        }
    }

    return {
        ...d,
        gre_url: url,
        match_method: matchMethod
    };
});

fs.writeFileSync("gre_mapped_drafts_v3.json", JSON.stringify(mapped, null, 2));

const found = mapped.filter(m => m.gre_url).length;
console.log(`📊 Mappatura V3 completata.`);
console.log(`✅ URL trovati: ${found} su ${mapped.length}`);
console.log(`⚠️ URL mancanti: ${mapped.length - found}`);

if (found > 0) {
    console.log("\nEsempi trovati:");
    mapped.filter(m => m.gre_url).slice(0, 10).forEach(m => console.log(` - ${m.title} (${m.match_method}) -> ${m.gre_url}`));
}
