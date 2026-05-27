import fs from "fs";

const drafts = JSON.parse(fs.readFileSync("gre_mapped_drafts_v4.json", "utf8"));
const allLinks = JSON.parse(fs.readFileSync("gre_all_product_links.json", "utf8"));

// Helper function to extract a clean title from a Grepool URL
function urlToTitle(url: string) {
    const parts = url.split('/');
    let lastPart = parts[parts.length - 1];
    // Remove query params or hashes
    lastPart = lastPart.split('?')[0].split('#')[0];
    // Replace dashes with spaces
    return lastPart.replace(/-/g, ' ').toLowerCase();
}

function slugify(text: string) {
    return text.toString().toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '');
}

// Simple similarity helper
function similarity(s1: string, s2: string) {
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
  return (longerLength - editDistance(longer, shorter)) / parseFloat(longerLength.toString());
}

function editDistance(s1: string, s2: string) {
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

const mapped = drafts.map((d: any) => {
    if (d.gre_url) return d; // already mapped

    let bestMatch = null;
    let bestScore = 0;
    
    // Test match by slug / URL text
    const dSlug = slugify(d.title);
    const dTitle = d.title.toLowerCase();

    for (const link of allLinks) {
        // Skip non-product links
        if (link.includes('/information/') || link.includes('/contatto') || link.includes('/ricerca')) continue;

        const linkTitle = urlToTitle(link);
        
        // Direct inclusion
        if (link.toLowerCase().includes(dSlug) || dSlug.includes(urlToTitle(link).replace(/ /g, '-'))) {
            bestMatch = link;
            bestScore = 1; // perfect partial
            break;
        }

        // Fuzzy match on URL title vs Product Title
        const score = similarity(dTitle, linkTitle);
        if (score > 0.65 && score > bestScore) {
            bestScore = score;
            bestMatch = link;
        }
    }

    if (bestMatch && bestScore > 0.65) {
        return {
            ...d,
            gre_url: bestMatch,
            match_method: `URL Match (${Math.round(bestScore*100)}%)`
        };
    }

    return d;
});

fs.writeFileSync("gre_mapped_drafts_v6.json", JSON.stringify(mapped, null, 2));

const found = mapped.filter((m: any) => m.gre_url).length;
console.log(`📊 Mappatura V6 completata.`);
console.log(`✅ URL trovati: ${found} su ${mapped.length}`);
console.log(`⚠️ URL mancanti: ${mapped.length - found}`);

if (found > 0) {
    const newlyFound = mapped.filter((m: any) => m.gre_url && m.match_method && m.match_method.includes('URL Match'));
    console.log(`\nNuovi Trovati in questa passata: ${newlyFound.length}`);
    newlyFound.slice(0, 10).forEach((m: any) => console.log(` - ${m.title} -> ${m.gre_url}`));
}
