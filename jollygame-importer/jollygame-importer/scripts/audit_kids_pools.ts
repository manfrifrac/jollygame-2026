import fs from "fs";

const catalog = JSON.parse(fs.readFileSync("master_catalog_dump.json", "utf8"));

const kidsPools: any[] = [];
const regularPools: any[] = [];

// Keywords for kids/small inflatable pools
const KIDS_KEYWORDS = ["anelli", "sunset", "bambini", "baby", "gonfiabile", "inflabile", "piccola", "glow", "fungo", "arcobaleno", "unicorno", "balena", "lumaca"];

for (const p of catalog) {
    const title = p.title.toLowerCase();
    const tags = p.tags || [];
    
    // Process only products tagged as Pools or with Piscina in title
    if (tags.includes("Categoria:Piscine") || title.includes("piscina")) {
        const isKids = KIDS_KEYWORDS.some(k => title.includes(k));
        
        // Large inflatables like "Easy Set" or "Prisma" should be checked carefully
        // Usually, if it's "Easy Set" > 3 meters it's not a "kids pool" in the sense of small toys.
        // But the user specifically mentioned "Intex Anelli".
        
        if (isKids) {
            kidsPools.push({
                id: p.id,
                title: p.title,
                vendor: p.vendor,
                status: p.status
            });
        } else {
            regularPools.push({
                id: p.id,
                title: p.title,
                vendor: p.vendor,
                status: p.status
            });
        }
    }
}

console.log(`\n📊 AUDIT TIPOLOGIA PISCINE:`);
console.log(`✅ Piscine Professionali/Grandi: ${regularPools.length}`);
console.log(`🚫 Piscine Piccole/Bambini (Candidate rimozione): ${kidsPools.length}`);

if (kidsPools.length > 0) {
    console.log("\n❌ ELENCO PISCINE PICCOLE / GONFIABILI DA RIMUOVERE:");
    console.table(kidsPools.map(p => ({ Titolo: p.title, Marca: p.vendor, Stato: p.status })));
}

fs.writeFileSync("kids_pools_audit.json", JSON.stringify(kidsPools, null, 2));
