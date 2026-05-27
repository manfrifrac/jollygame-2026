import fs from "fs";
import { parse } from "csv-parse/sync";

const drafts = JSON.parse(fs.readFileSync("gre_drafts_to_scrape.json", "utf8"));

// Files to check for URLs
const mappingFiles = [
    "mapping_prodotti_jolly_gre_FINALE.csv",
    "gre_alignment_final_report.csv"
];

const allRecords: any[] = [];

for (const file of mappingFiles) {
    if (fs.existsSync("../../" + file)) {
        const content = fs.readFileSync("../../" + file, "utf8");
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

const mapped = drafts.map(d => {
    let url = null;
    let matchMethod = "none";

    // 1. Match by SKU
    if (d.sku) {
        const match = allRecords.find(r => 
            (r.SKU && r.SKU.trim().toUpperCase() === d.sku.trim().toUpperCase())
        );
        if (match) {
            url = match.Grepool_URL || match.url || match.URL_Grepool;
            if (url) matchMethod = "SKU exact";
        }
    }

    // 2. Match by Handle (extract from Shopify_URL_Attuale or Shopify_Current_Handle)
    if (!url) {
        const match = allRecords.find(r => {
            const rShopifyUrl = r.Shopify_URL_Attuale || r.Shopify_Current_Handle || "";
            return rShopifyUrl.includes(d.handle);
        });
        if (match) {
            url = match.Grepool_URL || match.url || match.URL_Grepool;
            if (url) matchMethod = "Handle match";
        }
    }

    // 3. Match by Title
    if (!url) {
        const match = allRecords.find(r => {
            const rTitle = (r.Titolo || r.title || r.Title || "").toLowerCase();
            const dTitle = d.title.toLowerCase();
            return rTitle && (rTitle.includes(dTitle) || dTitle.includes(rTitle));
        });
        if (match) {
            url = match.Grepool_URL || match.url || match.URL_Grepool;
            if (url) matchMethod = "Title match";
        }
    }

    return {
        ...d,
        gre_url: url,
        match_method: matchMethod
    };
});

fs.writeFileSync("gre_mapped_drafts_v4.json", JSON.stringify(mapped, null, 2));

const found = mapped.filter(m => m.gre_url).length;
console.log(`📊 Mappatura V4 completata.`);
console.log(`✅ URL trovati: ${found} su ${mapped.length}`);
console.log(`⚠️ URL mancanti: ${mapped.length - found}`);

if (found > 0) {
    console.log("\nEsempi trovati:");
    mapped.filter(m => m.gre_url).slice(0, 10).forEach(m => console.log(` - ${m.title} (${m.match_method}) -> ${m.gre_url}`));
}
