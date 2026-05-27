import fs from "fs";

async function generateExhaustiveCSVFinal() {
  console.log("📊 Generazione Esportazione ABSOLUTE (Nessun campo escluso)...");
  
  const data = JSON.parse(fs.readFileSync("complete_data_dump.json", "utf8"));
  
  // 1. Identifichiamo tutti i Metafield unici
  const allMfKeys = new Set<string>();
  data.forEach((p: any) => {
    if (p.metafields?.nodes) {
      p.metafields.nodes.forEach((m: any) => {
        if (m) allMfKeys.add(`${m.namespace}.${m.key}`);
      });
    }
  });
  const mfColumns = Array.from(allMfKeys).sort();

  // 2. Definizione Headers (Esaustivo)
  const headers = [
    'Product ID', 'Variant ID', 'Handle', 'Status', 'Title', 'Vendor', 'Product Type', 'Tags',
    'SKU', 'Barcode (EAN)', 'Price', 'Compare at Price', 'Inventory Policy', 'Tracked (Inventory)', 
    'Option 1 Name', 'Option 1 Value', 'Option 2 Name', 'Option 2 Value', 'Featured Image URL',
    ...mfColumns.map(k => `MF: ${k}`),
    'Description (HTML)'
  ];

  let csv = headers.join(';') + '\n';

  data.forEach((p: any) => {
    const mfMap: Record<string, string> = {};
    if (p.metafields?.nodes) {
      p.metafields.nodes.forEach((m: any) => {
        if (m) mfMap[`${m.namespace}.${m.key}`] = m.value;
      });
    }

    const featuredImage = p.featuredMedia?.preview?.image?.url || "";

    p.variants.nodes.forEach((v: any) => {
      const row = [
        p.id,
        v.id,
        p.handle,
        p.status,
        p.title.replace(/;/g, ','),
        p.vendor,
        p.productType,
        (p.tags || []).join(',').replace(/;/g, ','),
        v.sku || "",
        v.barcode || "",
        v.price,
        v.compareAtPrice || "",
        v.inventoryPolicy,
        v.inventoryItem?.tracked ? "YES" : "NO",
        p.options?.[0]?.name || "",
        v.selectedOptions?.[0]?.value || "",
        p.options?.[1]?.name || "",
        v.selectedOptions?.[1]?.value || "",
        featuredImage,
        // Metafields
        ...mfColumns.map(k => (mfMap[k] || "").replace(/[\n\r]/g, ' ').replace(/;/g, ',')),
        (p.descriptionHtml || "").replace(/[\n\r]/g, ' ').replace(/;/g, ',')
      ];
      csv += row.join(';') + '\n';
    });
  });

  const finalPath = "../../Esportazione_COMPLETA_JollyGame_2026.csv";
  fs.writeFileSync(finalPath, csv, 'utf8');
  console.log(`\n✅ PERFETTO. Tutto il database è stato esportato.`);
  console.log(`📍 Path: ${finalPath}`);
  console.log(`🔢 Totale righe: ${csv.split('\n').length - 1}`);
  console.log(`📋 Metafield inclusi: ${mfColumns.length}`);
}

generateExhaustiveCSVFinal().catch(console.error);
