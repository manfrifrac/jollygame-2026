import fs from "fs";
import path from "path";

function prepareZodiacTargets() {
  console.log("🎯 Preparazione target per audit prezzi Zodiac...");

  const auditPath = path.resolve("catalog_visibility_report.json");
  const oldAuditPath = path.resolve("../../audit_results_v2.json");

  if (!fs.existsSync(auditPath) || !fs.existsSync(oldAuditPath)) {
      console.error("❌ File necessari non trovati.");
      return;
  }

  const visibilityData = JSON.parse(fs.readFileSync(auditPath, "utf-8"));
  const oldAuditData = JSON.parse(fs.readFileSync(oldAuditPath, "utf-8"));
  
  const zeroPriceZodiac = visibilityData.details.filter((p: any) => p.price === 0);
  const targets = [];

  for (const item of zeroPriceZodiac) {
    // Cerchiamo l'URL nell'audit vecchio per titolo
    const match = oldAuditData.find((a: any) => a.title.toLowerCase().trim() === item.title.toLowerCase().trim());
    
    if (match && match.url) {
      targets.push({
        title: item.title,
        handle: item.handle,
        sku: item.sku,
        url: match.url
      });
    }
  }

  const uniqueTargets = Array.from(new Map(targets.map(t => [t.url, t])).values());

  fs.writeFileSync("price_audit_targets.json", JSON.stringify(uniqueTargets, null, 2));
  console.log(`✅ Preparati ${uniqueTargets.length} target Zodiac per l'audit prezzi.`);
}

prepareZodiacTargets();
