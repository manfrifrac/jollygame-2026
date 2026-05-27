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

async function refineEmptyCollections() {
  const data = JSON.parse(fs.readFileSync("master_catalog_dump.json", "utf8"));
  const greProducts = data.filter((p: any) => p.vendor === "Gre");

  console.log(`🧹 Rifinitura tag per collezioni vuote...`);

  let updatedCount = 0;

  for (const p of greProducts) {
      const title = p.title.toLowerCase();
      const tags: string[] = p.tags || [];
      const newTags = new Set(tags);

      // 1. Piscine Interrate
      if (title.includes("interrata") || title.includes("interrate") || title.includes("sumatra") || title.includes("madagascar")) {
          newTags.add("Sottocategoria:Piscine interrate");
      }

      // 2. Elettrolisi e Sale
      if (title.includes("sale") || title.includes("elettrolisi") || title.includes("clorinatore")) {
          newTags.add("Sottocategoria:Elettrolisi del sale");
          newTags.add("Categoria:Trattamento acqua");
      }

      // 3. UV Disinfezione
      if (title.includes(" uv ") || title.includes("ultravioletti")) {
          newTags.add("Sottocategoria:Disinfezione per UV");
          newTags.add("Categoria:Trattamento acqua");
      }

      // 4. Materiale di pulizia (Retini, ecc.)
      if (title.includes("retino") || title.includes("spazzola") || title.includes("raccoglitore")) {
          newTags.add("Sottocategoria:Materiale di pulizia");
          newTags.add("Categoria:Pulitori");
      }

      if (newTags.size > tags.length) {
          await shopifyRequest(`
          mutation productUpdate($input: ProductInput!) {
            productUpdate(input: $input) {
              product { id }
              userErrors { message }
            }
          }
          `, {
              input: { id: p.id, tags: Array.from(newTags) }
          });
          updatedCount++;
      }
  }

  console.log(`\n✅ Rifinitura completata. ${updatedCount} prodotti aggiornati.`);
}

refineEmptyCollections().catch(console.error);
