import fs from "fs";

const catalog = JSON.parse(fs.readFileSync("master_catalog_dump.json", "utf8"));

const healthReport: any[] = [];

// Keywords for AI Leakage detection (more specific to avoid false positives)
const AI_PATTERNS = ["->", "diventa:", "nuovo titolo:", "riscrivilo", "ottimizzata:", "ecco una descrizione", "coprywriter", "specialista seo", "[inserisci", "sku: [", "rispondi solo con"];

for (const p of catalog) {
    const issues: string[] = [];
    const title = p.title.toLowerCase();
    const desc = (p.descriptionHtml || "").toLowerCase();
    const tags = p.tags || [];

    // 1. CONTENT CHECK
    if (AI_PATTERNS.some(pat => title.includes(pat))) issues.push("AI_LEAKAGE_TITLE");
    if (AI_PATTERNS.some(pat => desc.includes(pat))) issues.push("AI_LEAKAGE_DESCRIPTION");
    if (p.title.length < 5) issues.push("TITLE_TOO_SHORT");
    if (!p.descriptionHtml || p.descriptionHtml.length < 50) issues.push("DESC_TOO_SHORT_OR_MISSING");

    // 2. VISUAL & SAFETY
    // Note: prices are not in the master dump fields we requested usually, but we have mediaCount
    // Let's assume we want to know if images are missing
    // if (p.mediaCount?.count === 0) issues.push("MISSING_IMAGES"); // We don't have mediaCount in previous export? Let's check p fields.
    // I requested mediaCount in export_master_catalog.ts? No, I requested it in audit scripts but let me check master dump fields.
    
    // Actually, I'll use the fields I have.
    
    // 3. CATEGORIZATION
    const hasCategory = tags.some((t: string) => t.startsWith("Categoria:"));
    const hasSubCategory = tags.some((t: string) => t.startsWith("Sottocategoria:"));
    
    if (!hasCategory) issues.push("MISSING_CATEGORY_TAG");
    if (!hasSubCategory && !title.includes("piscina")) issues.push("MISSING_SUBCATEGORY_TAG");

    // 4. VENDOR & STATUS
    if (!p.vendor) issues.push("MISSING_VENDOR");
    
    // 5. SPECIFIC POOL CHECK
    if (tags.includes("Categoria:Piscine")) {
        const forbidden = ["telo", "copertura", "liner", "pompa", "filtro", "robot"];
        if (forbidden.some(k => title.includes(k))) issues.push("ACCESSORY_IN_POOL_CATEGORY");
    }

    healthReport.push({
        id: p.id,
        title: p.title,
        status: p.status,
        vendor: p.vendor,
        issues: issues,
        score: Math.max(0, 100 - (issues.length * 20))
    });
}

const critical = healthReport.filter(r => r.issues.length > 0);

console.log(`\n📊 REPORT SALUTE CATALOGO (268 prodotti analizzati):`);
console.log(`✅ Prodotti Perfetti: ${healthReport.length - critical.length}`);
console.log(`⚠️  Prodotti con Anomalie: ${critical.length}`);

if (critical.length > 0) {
    console.log("\n❌ DETTAGLIO ANOMALIE (Top 30):");
    console.table(critical.slice(0, 30).map(c => ({
        Prodotto: c.title.substring(0, 40),
        Stato: c.status,
        Problemi: c.issues.join(", ")
    })));
}

fs.writeFileSync("final_product_by_product_report.json", JSON.stringify(healthReport, null, 2));
