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

async function zeroToleranceCleanup() {
    const collectionId = "gid://shopify/Collection/686008336732"; // Piscine fuori terra
    console.log("🚫 AVVIO PULIZIA ZERO-TOLERANCE CATEGORIA PISCINE...");

    const query = `{
        collection(id: "${collectionId}") {
            products(first: 250) {
                nodes {
                    id
                    title
                    tags
                }
            }
        }
    }`;

    const res = await shopifyRequest(query);
    const products = res.data?.collection?.products?.nodes || [];

    const intruders: any[] = [];
    const forbiddenKeywords = [
        "accessori", "pompe", "kit", "copertore", "controllo", "scalette", 
        "telo", "filtro", "liner", "raccordo", "pulitore", "spazzola", 
        "aspiratore", "chimic", "cloro", "bromo", "trattamento", "tappeto",
        "copertura", "proiettore", "led", "luce", "termometro", "cartuccia",
        "manicotto", "giunzione", "skimmer", "manico", "avvolgitore", "protezione"
    ];

    for (const p of products) {
        const title = p.title.toLowerCase();
        
        // Se contiene una parola proibita E non è un'eccezione (es. "Piscina [Modello]")
        // Ma qui vogliamo essere severi: se il titolo dice "Accessori Piscina" o "Pompe per Piscina", via.
        const isActuallyAPool = (title.startsWith("piscina") || ["easy set", "prisma", "ultra xtr", "graphite", "lili", "grenade", "marbella", "vermela", "city", "mint", "sicilia", "pacific", "fidji", "bora bora", "haiti", "atlantis", "mauritius", "varadero", "granada", "avantgarde", "dolcevita", "bluespring", "ninfea", "pop!", "classic", "playa", "professional", "musa", "antea"].some(k => title.includes(k)))
                                && !forbiddenKeywords.some(k => title.includes(k));

        // Se la logica sopra dice che NON è una piscina, o se contiene esplicitamente una parola proibita
        if (forbiddenKeywords.some(k => title.includes(k)) || !isActuallyAPool) {
            intruders.push(p);
        }
    }

    console.log(`⚠️  Trovati ${intruders.length} intrusi nella collezione Piscine.`);

    for (const intruder of intruders) {
        console.log(`📍 RIMOZIONE FORZATA: ${intruder.title}`);
        
        // 1. Rimuoviamo i tag che lo portano in questa collezione
        const cleanTags = intruder.tags.filter((t: string) => 
            t !== "Categoria:Piscine" && 
            !t.startsWith("Sottocategoria:Piscine")
        );

        // 2. Cerchiamo di capire dove deve andare veramente
        const title = intruder.title.toLowerCase();
        const newTags = [...cleanTags];
        
        if (title.includes("pompa") || title.includes("filtro") || title.includes("cartuccia")) {
            newTags.push("Categoria:Filtraggio");
        } else if (title.includes("kit") || title.includes("trattamento") || title.includes("cloro")) {
            newTags.push("Categoria:Trattamento acqua");
        } else if (title.includes("copertura") || title.includes("telo") || title.includes("copri")) {
            newTags.push("Categoria:Coperture");
        } else {
            newTags.push("Categoria:Accessori");
            newTags.push("Sottocategoria:Altri accessori");
        }

        const mutation = `
        mutation productUpdate($input: ProductInput!) {
          productUpdate(input: $input) {
            product { id }
            userErrors { message }
          }
        }
        `;

        await shopifyRequest(mutation, {
            input: {
                id: intruder.id,
                tags: Array.from(new Set(newTags))
            }
        });
    }

    console.log("\n✅ Pulizia completata. La collezione Piscine è ora pura.");
}

zeroToleranceCleanup().catch(console.error);
