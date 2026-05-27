import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";

function prepareMassiveTargets() {
  console.log("🎯 Preparazione target massivi per audit prezzi...");
  
  const auditPath = path.resolve("catalog_visibility_report.json");
  const grePath = path.resolve("../../estrazione_sku_completa.csv");
  const netrivalsPath = path.resolve("../../all_decoded_netrivals_links.csv");

  if (!fs.existsSync(auditPath)) {
      console.error("❌ catalog_visibility_report.json non trovato.");
      return;
  }

  const visibilityData = JSON.parse(fs.readFileSync(auditPath, "utf-8"));
  const zeroPriceProducts = visibilityData.details.filter((p: any) => p.price === 0);
  
  const skuToUrl = new Map();
  if (fs.existsSync(grePath)) {
    const greRecords = parse(fs.readFileSync(grePath, "utf-8"), { columns: true });
    greRecords.forEach((r: any) => skuToUrl.set(r.SKU, r.Gre_URL));
  }

  const titleToUrl = new Map();
  if (fs.existsSync(netrivalsPath)) {
      const nrRecords = parse(fs.readFileSync(netrivalsPath, "utf-8"), { columns: true });
      nrRecords.forEach((r: any) => {
          if (r.Decoded_URL) titleToUrl.set(r.StoreName?.toLowerCase(), r.Decoded_URL);
      });
  }

  const targets = [];
  for (const item of zeroPriceProducts) {
    // 1. Cerchiamo per SKU (Grepool)
    let url = skuToUrl.get(item.sku);
    
    // 2. Se non abbiamo URL, proviamo a cercarlo nei link Netrivals per titolo (approssimativo)
    if (!url) {
        // Cerchiamo una corrispondenza parziale nel titolo dei link Netrivals
        // Questa è una euristica per trovare link alternativi
    }

    if (url) {
      targets.push({
        title: item.title,
        handle: item.handle,
        sku: item.sku,
        url: url
      });
    }
  }

  // Deduplicazione URL
  const uniqueTargets = Array.from(new Map(targets.map(t => [t.url, t])).values());

  fs.writeFileSync("price_audit_targets.json", JSON.stringify(uniqueTargets, null, 2));
  console.log(`✅ Preparati ${uniqueTargets.length} target per l'audit prezzi.`);
}

prepareMassiveTargets();
