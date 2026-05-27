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

// Simple similarity helper
function similarity(s1, s2) {
  let longer = s1;
  let shorter = s2;
  if (s1.length < s2.length) {
    longer = s2;
    shorter = s1;
  }
  let longerLength = longer.length;
  if (longerLength == 0) {
    return 1.0;
  }
  return (longerLength - editDistance(longer, shorter)) / parseFloat(longerLength);
}

function editDistance(s1, s2) {
  s1 = s1.toLowerCase();
  s2 = s2.toLowerCase();

  let costs = new Array();
  for (let i = 0; i <= s1.length; i++) {
    let lastValue = i;
    for (let j = 0; j <= s2.length; j++) {
      if (i == 0)
        costs[j] = j;
      else {
        if (j > 0) {
          let newValue = costs[j - 1];
          if (s1.charAt(i - 1) != s2.charAt(j - 1))
            newValue = Math.min(Math.min(newValue, lastValue),
              costs[j]) + 1;
          costs[j - 1] = lastValue;
          lastValue = newValue;
        }
      }
    }
    if (i > 0)
      costs[s2.length] = lastValue;
  }
  return costs[s2.length];
}

const mapped = drafts.map(d => {
    let url = null;
    let matchMethod = "none";
    let bestScore = 0;

    // 1. SKU Exact
    if (d.sku) {
        const match = allRecords.find(r => (r.SKU || r.sku || "").toUpperCase() === d.sku.toUpperCase());
        if (match) {
            url = match.Grepool_URL || match.url || match.URL_Grepool;
            if (url) matchMethod = "SKU exact";
        }
    }

    // 2. Fuzzy Title
    if (!url) {
        for (const r of allRecords) {
            const rTitle = (r.Titolo || r.title || r.Title || "").toLowerCase();
            if (!rTitle) continue;
            const dTitle = d.title.toLowerCase();
            const score = similarity(rTitle, dTitle);
            if (score > 0.8 && score > bestScore) {
                bestScore = score;
                url = r.Grepool_URL || r.url || r.URL_Grepool;
                matchMethod = `Fuzzy Title (${Math.round(score*100)}%)`;
            }
        }
    }

    return {
        ...d,
        gre_url: url,
        match_method: matchMethod
    };
});

fs.writeFileSync("gre_mapped_drafts_fuzzy.json", JSON.stringify(mapped, null, 2));

const found = mapped.filter(m => m.gre_url).length;
console.log(`📊 Mappatura Fuzzy completata.`);
console.log(`✅ URL trovati: ${found} su ${mapped.length}`);
console.log(`⚠️ URL mancanti: ${mapped.length - found}`);

if (found > 0) {
    console.log("\nEsempi trovati:");
    mapped.filter(m => m.gre_url).slice(0, 10).forEach(m => console.log(` - ${m.title} (${m.match_method}) -> ${m.gre_url}`));
}
