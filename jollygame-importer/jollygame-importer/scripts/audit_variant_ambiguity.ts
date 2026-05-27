import fs from "fs";
import dotenv from "dotenv";

dotenv.config();

async function auditVariantAmbiguity() {
    const data = JSON.parse(fs.readFileSync("master_catalog_dump.json", "utf8"));
    const greProducts = data.filter((p: any) => p.vendor === "Gre" && p.variants.nodes.length > 0);

    console.log("🔍 Analisi dettagliata varianti (Controllo Dimensione vs Dotazione)...");

    const report: any[] = [];

    for (const p of greProducts) {
        const variants = p.variants.nodes;
        
        // Raggruppiamo per titolo visualizzato
        const titleGroups: Record<string, any[]> = {};
        for (const v of variants) {
            const t = v.title || "Standard";
            if (!titleGroups[t]) titleGroups[t] = [];
            titleGroups[t].push(v);
        }

        for (const title in titleGroups) {
            const group = titleGroups[title];
            if (group.length > 1) {
                report.push({
                    prodotto: p.title,
                    variante_ambigua: title,
                    count: group.length,
                    skus: group.map(v => v.sku).join(", ")
                });
            }
        }
    }

    if (report.length > 0) {
        console.log("\n⚠️ RILEVATE VARIANTI CON LO STESSO NOME (AMBIGUE):");
        console.table(report);
    } else {
        console.log("\n✅ Nessuna variante con nome duplicato rilevata.");
    }

    // Secondo controllo: Varianti che sono solo una dimensione ma potrebbero avere differenze tecniche
    console.log("\n🔎 Controllo potenziali omissioni tecniche (es. Filtro)...");
    // (Qui dovrei cross-referenziare con l'Excel, ma iniziamo a vedere se ci sono casi sospetti)
}

auditVariantAmbiguity();
