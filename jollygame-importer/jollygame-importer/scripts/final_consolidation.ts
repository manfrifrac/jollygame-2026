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

function classifyGre(title: string, sku: string): string | null {
    const t = title.toLowerCase();
    const s = sku.toUpperCase();
    
    // NORDIC
    if (t.includes("nordic")) {
        if (s.includes("88") || t.includes("omega")) return "Islanda (Nordic Omega)";
        return "Greenland (Nordic Pali)";
    }
    // ANTRACITE
    if (t.includes("antracite") || t.includes("grigio") || t.includes("kea") || t.includes("skyathos")) {
        if (s.includes("88") || t.includes("omega") || t.includes("skyathos")) return "Skyathos (Antracite Omega)";
        return "Kea (Antracite Pali)";
    }
    // LEGNO
    if (t.includes("legno") || t.includes("mauritius") || t.includes("amazonia")) {
        if (s.includes("88") || t.includes("omega") || t.includes("amazonia")) return "Amazonia (Legno Omega)";
        return "Mauritius (Legno Pali)";
    }
    // BIANCA
    if (t.includes("atlantis") || t.includes("fidji") || t.includes("haiti") || t.includes("bora bora") || (t.includes("bianca") && t.includes("acciaio"))) {
        if (s.includes("88") || t.includes("omega") || t.includes("atlantis") || t.includes("haiti")) return "Atlantis/Haiti (Bianca Omega)";
        return "Fidji/Bora Bora (Bianca Pali)";
    }
    
    return null;
}

async function finalConsolidation() {
  console.log("🚀 Consolidamento Serie Gre (LOGICA POTENZIATA)...");

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
          variants(first: 20) { nodes { id sku price } }
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

  const groups: Record<string, any[]> = {};
  for (const p of allGreProducts) {
      const sku = p.variants.nodes[0]?.sku || "";
      const series = classifyGre(p.title, sku);
      if (series) {
          if (!groups[series]) groups[series] = [];
          groups[series].push(p);
      }
  }

  console.log(`📊 Trovate ${Object.keys(groups).length} serie commerciali.`);

  for (const series in groups) {
      const products = groups[series];
      if (products.length <= 1) continue;

      console.log(`\n📦 Consolidando: ${series} (${products.length} prodotti)`);
      
      const master = products[0];
      const others = products.slice(1);
      const variantsToAdd: any[] = [];

      for (const other of others) {
          for (const v of other.variants.nodes) {
              // Estrazione dimensione pulita
              const dimMatch = other.title.match(/(\d+x\d+)/) || other.title.match(/ø\s*(\d+)/i);
              let dim = dimMatch ? dimMatch[0] : "Standard";
              if (other.title.includes("730")) dim = "730x375";
              else if (other.title.includes("610")) dim = "610x375";
              else if (other.title.includes("500")) dim = "500x300";
              else if (other.title.includes("550")) dim = "Ø 550";
              else if (other.title.includes("460")) dim = "Ø 460";
              else if (other.title.includes("350")) dim = "Ø 350";

              variantsToAdd.push({
                  sku: v.sku,
                  price: v.price,
                  optionValues: [{ name: dim, optionName: "Misura" }],
                  inventoryPolicy: "CONTINUE"
              });
          }
      }

      // Update Master Title
      await shopifyRequest(`mutation productUpdate($input: ProductInput!) { productUpdate(input: $input) { product { id } } }`, {
          input: { id: master.id, title: `Piscina Gre Serie ${series}`, options: ["Misura"] }
      });

      // Add Variants
      const res = await shopifyRequest(`mutation productVariantsBulkCreate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) { productVariantsBulkCreate(productId: $productId, variants: $variants) { userErrors { message } } }`, {
          productId: master.id,
          variants: variantsToAdd
      });

      if (!res.data?.productVariantsBulkCreate?.userErrors?.length) {
          console.log(`   ✅ Varianti aggiunte. Elimino doppioni...`);
          for (const other of others) {
              await shopifyRequest(`mutation { productDelete(input: { id: "${other.id}" }) { deletedProductId } }`);
          }
      } else {
          console.error(`   ❌ Errore:`, res.data.productVariantsBulkCreate.userErrors);
      }
  }
}

finalConsolidation().catch(console.error);
