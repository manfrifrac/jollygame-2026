import fs from "fs";

async function generateMasterCSVFinal() {
  console.log("📊 Generazione CSV Master con Logica di Navigazione...");
  
  const data = JSON.parse(fs.readFileSync("master_catalog_dump.json", "utf8"));
  
  const headers = [
    'Product ID', 'Variant ID', 'Handle', 'Title', 'Status', 'Vendor', 'Type', 
    'NAV: Categoria', 'NAV: Sottocategoria', 'SEO: Search Boost Keywords', 'Tags (Altri)',
    'SKU', 'Price', 'Compare at Price',
    'Option 1 Name', 'Option 1 Value', 'Option 2 Name', 'Option 2 Value',
    'MF: Short Description', 'MF: Forma', 'MF: Materiale', 'MF: Volume Acqua', 'MF: Altezza Vasca',
    'MF: Portata Filtro', 'MF: Spessore Liner', 'MF: Dimensioni Esterne', 'MF: Serie Prodotto',
    'MF: Technical Specs (JSON)', 'MF: Exploded View URL', 'Description (HTML)'
  ];

  let csv = headers.join(';') + '\n';

  data.forEach((p: any) => {
    const mf: Record<string, string> = {};
    if (p.metafields) {
      p.metafields.forEach((m: any) => {
        if (m) mf[m.namespace + "." + m.key] = m.value;
      });
    }

    // Estrazione Tag di Navigazione
    const tags = p.tags || [];
    let categoria = "";
    let sottocategoria = "";
    const otherTags: string[] = [];

    tags.forEach((t: string) => {
        if (t.startsWith("Categoria:")) categoria = t.replace("Categoria:", "");
        else if (t.startsWith("Sottocategoria:")) sottocategoria = t.replace("Sottocategoria:", "");
        else otherTags.push(t);
    });

    const searchBoost = mf["shopify--discovery--product_search_boost.queries"] || "";

    p.variants.nodes.forEach((v: any) => {
      const row = [
        p.id,                                     // Product ID
        v.id,                                     // Variant ID
        p.handle,                                 // Handle
        p.title.replace(/;/g, ','),               // Title
        p.status,                                 // Status
        p.vendor,                                 // Vendor
        p.productType,                            // Type
        categoria,                                // NAV: Categoria
        sottocategoria,                           // NAV: Sottocategoria
        searchBoost.replace(/;/g, ','),           // SEO: Search Boost
        otherTags.join(',').replace(/;/g, ','),   // Tags (Altri)
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
  console.log(`✅ CSV di Navigazione creato! Totale righe: ${data.length}`);
}

generateMasterCSVFinal().catch(console.error);
