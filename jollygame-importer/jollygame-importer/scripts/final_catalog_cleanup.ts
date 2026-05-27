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

const FINAL_CLEANUP = [
    { title: "Cartuccie Chlorinanti Intex", target: "Categoria:Trattamento acqua" },
    { title: "Aspirapolvere Intex", target: "Categoria:Pulitori" },
    { title: "Kit Pulizia Intex", target: "Categoria:Pulitori" },
    { title: "Piscina Robot RA 6500 iQ", target: "Categoria:Pulitori" },
    { title: "Bicicletta Acquatica in Acciaio Inox", target: "Categoria:Accessori" },
    { title: "Barriera Di Protezione Flessibile", target: "Categoria:Accessori" },
    { title: "Tappeti In Poliestere", target: "Categoria:Coperture" },
    { title: "Tappeti Protettivi Rettangolari", target: "Categoria:Coperture" },
    { title: "Spugne Magiche", target: "Categoria:Accessori" },
    { title: "Doccia solare", target: "Categoria:Accessori" },
    { title: "Piscina quadrata copertura", target: "Categoria:Coperture" },
    { title: "Kit By Pass", target: "Categoria:Filtraggio" },
    { title: "Blue Fit 50", target: "Categoria:Trattamento acqua" },
    { title: "Estensore WiFi Bluetooth Blue", target: "Categoria:Trattamento acqua" },
    { title: "KIT trattamento piscina", target: "Categoria:Trattamento acqua" },
    { title: "Clorinatore salino collegato", target: "Categoria:Trattamento acqua" },
    { title: "Sistema filtrante Aqualoon", target: "Categoria:Filtraggio" },
    { title: "Deposito per filtri indipendenti", target: "Categoria:Filtraggio" },
    { title: "Deposito a sabbia per depurazione", target: "Categoria:Filtraggio" },
    { title: "Copertore per piscine rettangolari in legno Mint", target: "Categoria:Coperture" },
    { title: "Controllo remoto a 4 azioni", target: "Categoria:Accessori" },
    { title: "Elevatore di alcalinità", target: "Categoria:Trattamento acqua" },
    { title: "Protezione Delta MS", target: "Categoria:Coperture" },
    { title: "Scalette in legno", target: "Categoria:Accessori" },
    { title: "Aspiratori idraulici silenziosi Silence Vac", target: "Categoria:Pulitori" },
    { title: "Raccoglitore di fondo Eco Range", target: "Categoria:Pulitori" },
    { title: "Erogatore Flot 200 g", target: "Categoria:Accessori" },
    { title: "Doccia in acciaio inossidabile", target: "Categoria:Accessori" },
    { title: "Ovale 5390", target: "Categoria:Pulitori" } // È un robot Zodiac OV 5390
];

async function finalCatalogCleanup() {
    console.log("🧹 Avvio Pulizia Finale Definitiva...");

    for (const item of FINAL_CLEANUP) {
        // Cerca il prodotto per titolo parziale
        const query = `{
            products(first: 5, query: "title:'${item.title}'") {
                nodes {
                    id
                    title
                    tags
                }
            }
        }`;
        
        const res = await shopifyRequest(query);
        const products = res.data?.products?.nodes || [];

        for (const product of products) {
            console.log(`📍 Spostando: ${product.title} -> ${item.target}`);
            
            // Rimuoviamo tag piscina e aggiungiamo quello corretto
            let newTags = product.tags.filter((t: string) => 
                t !== "Categoria:Piscine" && 
                !t.startsWith("Sottocategoria:Piscine")
            );
            newTags.push(item.target);

            // Aggiungiamo sottocategoria specifica se possibile
            if (item.target === "Categoria:Trattamento acqua") newTags.push("Sottocategoria:Prodotti chimici");
            if (item.target === "Categoria:Filtraggio" && product.title.toLowerCase().includes("pompa")) newTags.push("Sottocategoria:Pompe per piscine");
            if (item.target === "Categoria:Filtraggio" && !product.title.toLowerCase().includes("pompa")) newTags.push("Sottocategoria:Filtri");
            if (item.target === "Categoria:Pulitori" && (product.title.toLowerCase().includes("robot") || product.title.toLowerCase().includes("ovale 5390"))) newTags.push("Sottocategoria:Pulitori elettrico");

            newTags = Array.from(new Set(newTags));

            const mutation = `
            mutation productUpdate($input: ProductInput!) {
              productUpdate(input: $input) {
                product { id }
                userErrors { message }
              }
            }
            `;
            await shopifyRequest(mutation, { input: { id: product.id, tags: newTags } });
        }
    }

    console.log("\n🎉 Catalogo ora 100% Coerente e Pulito.");
}

finalCatalogCleanup().catch(console.error);
