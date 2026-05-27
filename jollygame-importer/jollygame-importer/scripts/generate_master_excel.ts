import fs from "fs";
import * as xlsx from "xlsx";

async function generateMasterExcel() {
  console.log("📊 Generazione Excel Master per editing massivo...");
  
  const data = JSON.parse(fs.readFileSync("master_catalog_dump.json", "utf8"));
  const rows: any[] = [];

  for (const p of data) {
    // Estrazione metafields comuni
    const metafields: Record<string, string> = {};
    if (p.metafields) {
      p.metafields.forEach((m: any) => {
        if (m) metafields[m.namespace + "." + m.key] = m.value;
      });
    }

    for (const v of p.variants.nodes) {
      rows.push({
        "Product ID": p.id,
        "Variant ID": v.id,
        "Handle": p.handle,
        "Title": p.title,
        "Status": p.status,
        "Vendor": p.vendor,
        "Type": p.productType,
        "Tags": (p.tags || []).join(", "),
        "SKU": v.sku,
        "Price": v.price,
        "Compare at Price": v.compareAtPrice,
        "Option 1 Name": p.options?.[0]?.name || "",
        "Option 1 Value": v.selectedOptions?.[0]?.value || "",
        "Option 2 Name": p.options?.[1]?.name || "",
        "Option 2 Value": v.selectedOptions?.[1]?.value || "",
        "Short Description": metafields["custom.short_description"] || "",
        "Technical Specs (JSON)": metafields["custom.additional_specs"] || "",
        "Exploded View URL": metafields["custom.immagine_esploso"] || "",
        "Manuals (JSON)": metafields["custom.documentazione_tecnica"] || "",
        "Description (HTML)": p.descriptionHtml || ""
      });
    }
  }

  const wb = xlsx.utils.book_new();
  const ws = xlsx.utils.json_to_sheet(rows);
  xlsx.utils.book_append_sheet(wb, ws, "Master Catalog");
  
  const filename = "../../Master_Export_JollyGame_2026.xlsx";
  xlsx.writeFile(wb, filename);

  console.log(`✅ File creato con successo: ${filename}`);
  console.log(`📋 Totale righe esportate: ${rows.length}`);
}

generateMasterExcel().catch(console.error);
