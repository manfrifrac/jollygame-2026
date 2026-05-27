import dotenv from "dotenv";

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

const FIXES = [
  {
    id: "gid://shopify/Product/15527770915164",
    title: "Adesivo specifico per PVC",
    descriptionHtml: "<p>Adesivo specifico per PVC per la riparazione e manutenzione di componenti in plastica della piscina. Garantisce una tenuta forte e duratura.</p>"
  },
  {
    id: "gid://shopify/Product/15527774126428",
    title: "Riscaldamento solare per piscine",
  },
  {
    id: "gid://shopify/Product/15527774191964",
    title: "Aspiratori idraulici silenziosi Silence Vac",
  },
  {
    id: "gid://shopify/Product/15527777173852",
    title: "Copertura per piscina rotonda violetta - Mod. 581",
  }
];

// Funzione per pulire descrizioni con leakage AI generico
function cleanDescription(html: string): string {
  if (!html) return html;
  // Rimuove frasi tipiche di leakage AI se presenti
  let cleaned = html;
  const patterns = [
    /Ecco una descrizione ottimizzata:?/gi,
    /Nuovo titolo:.*$/gim,
    /Rispondi solo con.*$/gim,
    /Sei un esperto di copywriting.*$/gim
  ];
  
  patterns.forEach(p => {
    cleaned = cleaned.replace(p, "");
  });
  
  return cleaned.trim();
}

async function fixAiLeakage() {
  console.log("🛠️ Correzione manuale dei titoli con AI Leakage...");

  for (const fix of FIXES) {
    console.log(`Updating ${fix.id}...`);
    const mutation = `
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product { id title }
        userErrors { message }
      }
    }
    `;

    const input: any = { id: fix.id, title: fix.title };
    if (fix.descriptionHtml) {
        input.descriptionHtml = fix.descriptionHtml;
    }

    const res = await shopifyRequest(mutation, { input });
    if (res.data?.productUpdate?.userErrors?.length > 0) {
      console.error(`❌ Errore aggiornamento ${fix.id}:`, res.data.productUpdate.userErrors);
    } else {
      console.log(`✅ Aggiornato: ${fix.title}`);
    }
  }

  // Ora cerchiamo descrizioni sporche
  console.log("\n🔍 Bonifica descrizioni con leakage AI...");
  const query = `{
    products(first: 250) {
      nodes {
        id
        title
        descriptionHtml
      }
    }
  }`;

  const res = await shopifyRequest(query);
  const products = res.data.products.nodes;

  for (const p of products) {
    if (!p.descriptionHtml) continue;
    
    const cleaned = cleanDescription(p.descriptionHtml);
    if (cleaned !== p.descriptionHtml) {
        console.log(`✨ Pulizia descrizione per: ${p.title}`);
        const mutation = `
        mutation productUpdate($input: ProductInput!) {
          productUpdate(input: $input) {
            product { id }
            userErrors { message }
          }
        }
        `;
        await shopifyRequest(mutation, { input: { id: p.id, descriptionHtml: cleaned } });
    }
  }

  console.log("\n✅ Bonifica AI completata!");
}

fixAiLeakage().catch(console.error);
