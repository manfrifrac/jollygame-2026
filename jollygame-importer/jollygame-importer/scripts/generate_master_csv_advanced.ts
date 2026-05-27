import fs from "fs";

async function generateMasterCSV() {
  console.log("📊 Generazione CSV Master con Metafields avanzati...");
  
  const data = JSON.parse(fs.readFileSync("master_catalog_dump.json", "utf8"));
  
  // Header definitivi
  const headers = [
    'Product ID', 'Variant ID', 'Handle', 'Title', 'Status', 'Vendor', 'Type', 'Tags', 'SKU', 'Price', 'Compare at Price',
    'Option 1 Name', 'Option 1 Value', 'Option 2 Name', 'Option 2 Value',
    'MF: Short Description', 'MF: Forma', 'MF: Materiale', 'MF: Volume Acqua', 'MF: Altezza Vasca',
    'MF: Portata Filtro', 'MF: Spessore Liner', 'MF: Dimensioni Esterne', 'MF: Serie Prodotto',
    'MF: Technical Specs (JSON)', 'MF: Exploded View URL', 'Description (HTML)'
  ];

  let csv = headers.join(';') + '\n';

  data.forEach((p: any) => {
    // Mappa metafields per questo prodotto
    const mf: Record<string, string> = {};
    if (p.metafields) {
      p.metafields.forEach((m: any) => {
        if (m) mf[m.namespace + "." + m.key] = m.value;
      });
    }

    const baseRow = [
      p.id,
      p.handle,
      p.title.replace(/;/g, ','),
      p.status,
      p.vendor,
      p.productType,
      (p.tags || []).join(',').replace(/;/g, ','),
      mf["custom.short_description"] || "",
      mf["custom.forma"] || "",
      mf["custom.materiale"] || "",
      mf["custom.volume_acqua"] || "",
      mf["custom.altezza_vasca"] || "",
      mf["custom.portata_filtro"] || "",
      mf["custom.spessore_liner"] || "",
      mf["custom.dimensioni_esterne"] || "",
      mf["custom.serie_prodotto"] || "",
      (mf["custom.additional_specs"] || "").replace(/[\n\r]/g, ' ').replace(/;/g, ','),
      mf["custom.immagine_esploso"] || "",
      (p.descriptionHtml || "").replace(/[\n\r]/g, ' ').replace(/;/g, ',')
    ];

    p.variants.nodes.forEach((v: any) => {
      // Costruiamo la riga completa unendo i dati variante ai dati prodotto
      const row = [
        p.id,                                     // Product ID
        v.id,                                     // Variant ID
        p.handle,                                 // Handle
        p.title.replace(/;/g, ','),               // Title
        p.status,                                 // Status
        p.vendor,                                 // Vendor
        p.productType,                            // Type
        (p.tags || []).join(',').replace(/;/g, ','), // Tags
        v.sku || "",                              // SKU
        v.price,                                  // Price
        v.compareAtPrice || "",                    // Compare at Price
        p.options?.[0]?.name || "",               // Option 1 Name
        v.selectedOptions?.[0]?.value || "",      // Option 1 Value
        p.options?.[1]?.name || "",               // Option 2 Name
        v.selectedOptions?.[1]?.value || "",      // Option 2 Value
        mf["custom.short_description"] || "",
        mf["custom.forma"] || "",
        mf["custom.materiale"] || "",
        mf["custom.volume_acqua"] || "",
        mf["custom.altezza_vasca"] || "",
        mf["custom.portata_filtro"] || "",
        mf["custom.spessore_liner"] || "",
        mf["custom.dimensioni_esterne"] || "",
        mf["custom.serie_prodotto"] || "",
        (mf["custom.additional_specs"] || "").replace(/[\n\r]/g, ' ').replace(/;/g, ','),
        mf["custom.immagine_esploso"] || "",
        (p.descriptionHtml || "").replace(/[\n\r]/g, ' ').replace(/;/g, ',')
      ];
      csv += row.join(';') + '\n';
    });
  });

  fs.writeFileSync("../../Master_Export_JollyGame_2026.csv", csv, 'utf8');
  console.log(`✅ CSV aggiornato con successo! Righe: ${data.length}`);
}

generateMasterCSV().catch(console.error);
