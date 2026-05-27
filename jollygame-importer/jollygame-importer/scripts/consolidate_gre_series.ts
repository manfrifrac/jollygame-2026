import dotenv from "dotenv";
import fs from "fs";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

// Logica di classificazione serie
function classifySeries(title: string, sku: string): string | null {
    const t = title.toLowerCase();
    const s = sku.toUpperCase();
    
    if (t.includes("nordic")) {
        if (s.includes("88") || t.includes("omega")) return "Islanda (Nordic Omega)";
        return "Greenland (Nordic Pali)";
    }
    if (t.includes("antracite") || t.includes("grigio")) {
        if (s.includes("88") || t.includes("omega")) return "Skyathos (Antracite Omega)";
        return "Kea (Antracite Pali)";
    }
    if (t.includes("legno")) {
        if (s.includes("88") || t.includes("omega")) return "Amazonia (Legno Omega)";
        return "Mauritius (Legno Pali)";
    }
    if (t.includes("bianca") || t.includes("fidji") || t.includes("atlantis")) {
        if (s.includes("88") || t.includes("omega") || t.includes("atlantis")) return "Atlantis (Bianca Omega)";
        return "Fidji (Bianca Pali)";
    }
    return null;
}

async function consolidateSeries() {
  console.log("🚀 Inizio consolidamento serie Gre...");

  // 1. Scarica tutti i prodotti Gre attuali
  let hasNextPage = true;
  let cursor = null;
  const allGreProducts: any[] = [];

  while (hasNextPage) {
    const query = `
    query getGre($cursor: String) {
      products(first: 250, after: $cursor, query: "vendor:Gre") {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          descriptionHtml
          vendor
          tags
          status
          variants(first: 20) {
            nodes {
              id
              sku
              price
              inventoryPolicy
            }
          }
        }
      }
    }
    `;
    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;
    allGreProducts.push(...res.data.products.nodes);
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  // 2. Raggruppa per serie
  const seriesGroups: Record<string, any[]> = {};
  for (const p of allGreProducts) {
      const sku = p.variants.nodes[0]?.sku || "";
      const series = classifySeries(p.title, sku);
      if (series) {
          if (!seriesGroups[series]) seriesGroups[series] = [];
          seriesGroups[series].push(p);
      }
  }

  console.log(`📊 Trovate ${Object.keys(seriesGroups).length} serie commerciali da consolidare.`);

  for (const seriesName in seriesGroups) {
      const products = seriesGroups[seriesName];
      if (products.length <= 1) continue;

      console.log(`\n📦 Consolidamento serie: ${seriesName} (${products.length} modelli)`);
      
      // Il primo prodotto diventa il Master
      const master = products[0];
      const others = products.slice(1);

      // Raccogliamo tutte le varianti degli altri
      const variantsToAdd: any[] = [];
      for (const other of others) {
          for (const v of other.variants.nodes) {
              // Estraiamo la misura dal titolo dell'altro prodotto
              // Esempio title: "... Dim: 730x375 ..." -> "730x375"
              const dimMatch = other.title.match(/Dim:\s*([^h]+)/i) || other.title.match(/(\d+x\d+)/);
              const variantName = dimMatch ? dimMatch[1].trim() : other.title.split('.').pop()?.trim() || "Standard";
              
              variantsToAdd.push({
                  sku: v.sku,
                  price: v.price,
                  optionValues: [{ name: variantName, optionName: "Misura" }],
                  inventoryPolicy: "CONTINUE"
              });
          }
      }

      // 3. Aggiorna Master (Titolo pulito e opzioni)
      const updateMutation = `
      mutation productUpdate($input: ProductInput!) {
        productUpdate(input: $input) {
          product { id }
          userErrors { message }
        }
      }
      `;
      
      const cleanTitle = `Piscina Gre ${seriesName}`;
      await shopifyRequest(updateMutation, {
          input: {
              id: master.id,
              title: cleanTitle,
              options: ["Misura"]
          }
      });

      // 4. Aggiungi varianti al Master
      const addVariantsMutation = `
      mutation productVariantsBulkCreate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
        productVariantsBulkCreate(productId: $productId, variants: $variants) {
          productVariants { id }
          userErrors { message }
        }
      }
      `;
      
      const res = await shopifyRequest(addVariantsMutation, {
          productId: master.id,
          variants: variantsToAdd
      });

      if (!res.data?.productVariantsBulkCreate?.userErrors?.length) {
          console.log(`   ✅ Varianti aggiunte a ${cleanTitle}.`);
          // 5. Elimina i prodotti obsoleti
          for (const other of others) {
              const deleteMutation = `mutation { productDelete(input: { id: "${other.id}" }) { deletedProductId } }`;
              await shopifyRequest(deleteMutation);
          }
          console.log(`   🗑️  Eliminati ${others.length} prodotti duplicati/singoli.`);
      } else {
          console.error(`   ❌ Errore aggiunta varianti:`, res.data.productVariantsBulkCreate.userErrors);
      }
  }

  console.log("\n✅ Consolidamento completato!");
}

consolidateSeries().catch(console.error);
