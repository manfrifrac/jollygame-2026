import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";

function prepareTargets() {
  const auditPath = path.resolve("audit_quality_v2_report.json");
  const grePath = path.resolve("../../estrazione_sku_completa.csv");
  
  if (!fs.existsSync(auditPath)) {
      console.error(`❌ Audit report not found at ${auditPath}`);
      return;
  }
  if (!fs.existsSync(grePath)) {
    console.error(`❌ Gre SKU file not found at ${grePath}`);
    return;
}

  const auditReport = JSON.parse(fs.readFileSync(auditPath, "utf-8"));
  const greRecords = parse(fs.readFileSync(grePath, "utf-8"), { columns: true });
  
  const targets = [];
  const skuToUrl = new Map();
  greRecords.forEach((r: any) => skuToUrl.set(r.SKU, r.Gre_URL));

  for (const item of auditReport.details.missing_price) {
    if (item.sku && skuToUrl.has(item.sku)) {
      targets.push({
        handle: item.handle,
        title: item.product_title,
        sku: item.sku,
        url: skuToUrl.get(item.sku)
      });
    }
  }

  const uniqueTargets = Array.from(new Map(targets.map(t => [t.url, t])).values());

  fs.writeFileSync("price_audit_targets.json", JSON.stringify(uniqueTargets, null, 2));
  console.log(`✅ Preparati ${uniqueTargets.length} target per l'audit prezzi.`);
}

prepareTargets();
