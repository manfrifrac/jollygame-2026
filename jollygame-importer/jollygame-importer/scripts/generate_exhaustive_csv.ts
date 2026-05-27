import fs from "fs";

async function generateExhaustiveCSV() {
  console.log("📊 Generazione Esportazione TOTALE (EAN, Metafields, Logistica)...");
  
  const data = JSON.parse(fs.readFileSync("master_catalog_dump.json", "utf8"));
  
  // 1. Identifichiamo tutti i Metafield unici presenti nel dump per creare le colonne
  const allMfKeys = new Set<string>();
  data.forEach((p: any) => {
    if (p.metafields?.nodes) {
      p.metafields.nodes.forEach((m: any) => {
        if (m) allMfKeys.add(`${m.namespace}.${m.key}`);
      });
    }
  });
  const mfColumns = Array.from(allMfKeys).sort();

  // 2. Definizione Headers
  const headers = [
    'Product ID', 'Variant ID', 'Handle', 'Status', 'Title', 'Vendor', 'Product Type', 'Tags',
    'SKU', 'Barcode (EAN)', 'Price', 'Compare at Price', 'Weight', 'Weight Unit', 
    'Inventory Policy', 'Inventory Management', 'Option 1 Name', 'Option 1 Value', 
    'Option 2 Name', 'Option 2 Value', 'Featured Image URL',
    ...mfColumns.map(k => `MF: ${k}`),
    'Description (HTML)'
  ];

  let csv = headers.join(';') + '\n';

  data.forEach((p: any) => {
    // Mappa metafields per riga
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
        v.weight || "",
        v.weightUnit || "",
        v.inventoryPolicy,
        v.inventoryManagement,
        p.options?.[0]?.name || "",
        v.selectedOptions?.[0]?.value || "",
        p.options?.[1]?.name || "",
        v.selectedOptions?.[1]?.value || "",
        featuredImage,
        // Inserimento dinamico di tutti i metafields
        ...mfColumns.map(k => (mfMap[k] || "").replace(/[\n\r]/g, ' ').replace(/;/g, ',')),
        (p.descriptionHtml || "").replace(/[\n\r]/g, ' ').replace(/;/g, ',')
      ];
      csv += row.join(';') + '\n';
    });
  });

  const finalPath = "../../Esportazione_TOTALE_JollyGame_2026.csv";
  fs.writeFileSync(finalPath, csv, 'utf8');
  console.log(`\n✅ ECCELLENTE. Esportazione completata.`);
  console.log(`📍 Path: ${finalPath}`);
  console.log(`🔢 Righe: ${csv.split('\n').length - 1}`);
  console.log(`📋 Colonne Metafield rilevate: ${mfColumns.length}`);
}

generateExhaustiveCSV().catch(console.error);
