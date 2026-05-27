import dotenv from "dotenv";
import Groq from "groq-sdk";
import fs from "fs";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function auditContent(title: string, descriptionHtml: string, vendor: string, metafields: any[]) {
  try {
    const metaStr = metafields.map(m => `- ${m.namespace}.${m.key}: ${m.value}`).join("\n");
    const prompt = `Sei un esperto di e-commerce e SEO per il settore piscine. Analizza il prodotto Shopify seguente, inclusi i suoi campi tecnici (metafields).
    
    VENDOR: ${vendor}
    TITOLO: ${title}
    DESCRIZIONE (HTML): ${descriptionHtml.slice(0, 800)}
    CAMPI TECNICI (Metafields):
    ${metaStr || "Nessun campo tecnico specificato."}
    
    Obiettivi dell'audit:
    1. Valutare se il titolo è ottimizzato SEO e professionale.
    2. Verificare se la descrizione è persuasiva e contiene tutti i dati tecnici presenti nei metafields.
    3. Controllare la coerenza tra titolo, descrizione e campi tecnici.
    4. Suggerire miglioramenti per massimizzare le conversioni.

    Restituisci un oggetto JSON con questa struttura:
    {
      "rating_complessivo": (1-10),
      "analisi_critica": "testo dettagliato",
      "suggerimento_titolo": "nuovo titolo ottimizzato",
      "suggerimento_descrizione": "nuovo HTML ottimizzato (mantieni TUTTI i dati tecnici e usa tag h3, p, ul, li)",
      "suggerimenti_metafields": [
        { "namespace": "custom", "key": "key_da_aggiornare", "nuovo_valore": "valore suggerito", "motivo": "perché" }
      ]
    }
    
    Rispondi SOLO con il JSON, senza altri commenti.`;

    const completion = await groq.chat.completions.create({
      messages: [{ role: "user", content: prompt }],
      model: "llama-3.1-8b-instant",
      response_format: { type: "json_object" }
    });

    const content = completion.choices[0]?.message?.content;
    return content ? JSON.parse(content) : null;
  } catch (e: any) {
    if (e?.status === 429) {
        console.warn(`  ⚠️ Rate limit raggiunto. Attendo 30 secondi...`);
        await new Promise(r => setTimeout(r, 30000));
        return auditContent(title, descriptionHtml, vendor, metafields); // Riprova una volta
    }
    console.error(`  ❌ Errore Groq per ${title}:`, e);
    return null;
  }
}

async function runAudit() {
  console.log("🔍 Avvio Audit Qualità Avanzato (Titoli + Descrizioni + Metafields)...");

  const query = `
  query {
    products(first: 20) {
      nodes {
        id
        title
        vendor
        descriptionHtml
        handle
        metafields(first: 50) {
          nodes {
            namespace
            key
            value
          }
        }
      }
    }
  }
  `;

  const res = await shopifyRequest(query);
  if (!res.data?.products?.nodes) {
      console.error("Errore nel recupero prodotti:", JSON.stringify(res, null, 2));
      return;
  }
  
  const products = res.data.products.nodes;
  const auditResults = [];

  for (const product of products) {
    console.log(`\n⚖️ Analisi Completa: [${product.vendor}] ${product.title}`);
    
    const customMetafields = product.metafields.nodes.filter((m: any) => m.namespace === 'custom' || m.namespace === 'global');
    const audit = await auditContent(product.title, product.descriptionHtml, product.vendor, customMetafields);
    
    if (audit) {
        auditResults.push({
            id: product.id,
            original: {
                title: product.title,
                description: product.descriptionHtml,
                vendor: product.vendor,
                handle: product.handle,
                metafields: customMetafields
            },
            audit: audit
        });
        console.log(`  ⭐ Rating: ${audit.rating_complessivo}/10`);
        console.log(`  💡 Nuovo Titolo: ${audit.suggerimento_titolo}`);
        if (audit.suggerimenti_metafields?.length > 0) {
            console.log(`  ⚙️ Suggeriti ${audit.suggerimenti_metafields.length} aggiornamenti ai metafields.`);
        }
    }

    // Delay maggiore per evitare rate limits
    await new Promise(r => setTimeout(r, 3000));
  }

  fs.writeFileSync("audit_quality_report.json", JSON.stringify(auditResults, null, 2));
  console.log("\n✅ Audit completato! Report salvato in 'audit_quality_report.json'");
}

runAudit().catch(console.error);
