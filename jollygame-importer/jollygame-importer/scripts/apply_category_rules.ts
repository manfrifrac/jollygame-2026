import fs from "fs";

const products = JSON.parse(fs.readFileSync("product_category_review.json", "utf-8"));

const rules = [
    { keywords: ["robot", "aspirapolvere", "iq", "pulitore elettrico", "vortex", "alpha", "voyager", "cnx", "swy", "silence vac"], category: "Pulitori > Elettrici" },
    { keywords: ["pulitore manuale", "spazzola aspirante", "raccoglitore di fondo", "retino"], category: "Pulitori > Manuali" },
    { keywords: ["pompa di calore", "hpm", "inverter", "z250", "z350", "z400", "z550", "z650", "sirocco", "heat line", "riscaldamento solare"], category: "Riscaldamento > Pompe di Calore" },
    { keywords: ["elettrolisi", "sale", "exo", "ei2", "eisalt", "gensalt", "clorinatore"], category: "Trattamento Acqua > Elettrolisi" },
    { keywords: ["uv", "disinfezione"], category: "Trattamento Acqua > Sistemi UV" },
    { keywords: ["ph expert", "chlor expert", "dual link", "ph link", "analisi", "blue connect", "sonda", "blue fit", "tester", "regolatore ph"], category: "Trattamento Acqua > Analisi e Controllo" },
    { keywords: ["cloro", "bromo", "ossigeno", "anticalcare", "svernante", "flocculante", "alcalinità", "ph plus", "ph minus", "trattamento acqua", "adesivo", "colla"], category: "Trattamento Acqua > Prodotti Chimici" },
    { keywords: ["piscina", "legno", "sunbay", "antea", "marbella", "lili", "vermeille", "grenade", "mint"], category: "Piscine > Legno" },
    { keywords: ["piscina", "acciaio", "pacific", "sicilia", "sumatra", "atlantis", "amazonie", "anthracite", "hydrium", "ultra xtr", "graphite"], category: "Piscine > Acciaio" },
    { keywords: ["piscina", "composito", "avantgarde"], category: "Piscine > Composito" },
    { keywords: ["interrata", "piscina in pietra"], category: "Piscine > Interrate" },
    { keywords: ["liner"], category: "Componenti > Liner" },
    { keywords: ["copertura", "copertore", "telo", "avvolgitore"], category: "Componenti > Coperture" },
    { keywords: ["filtro", "depuratore", "monoblocco", "depurazione", "cartuccia filtrante", "aqualoon", "deposito"], category: "Filtrazione > Filtri" },
    { keywords: ["pompa", "flopro", "iqpump"], category: "Filtrazione > Pompe" },
    { keywords: ["casetta"], category: "Componenti > Casette Tecniche" },
    { keywords: ["raccordo", "unione", "tubo", "manicotto", "tappo", "valvola", "skimmer", "by pass"], category: "Componenti > Idraulica e Accessori" },
    { keywords: ["scaletta", "scala"], category: "Componenti > Scalette" },
    { keywords: ["doccia"], category: "Accessori > Docce" },
    { keywords: ["tappeto", "puzzle"], category: "Accessori > Tappeti e Protezioni" },
    { keywords: ["proiettore", "led", "lampada", "illuminazione"], category: "Accessori > Illuminazione" },
    { keywords: ["termometro", "dosatore", "spazzola", "manico", "kit riparazione", "spugne magiche", "barriera di protezione", "smart plug"], category: "Accessori > Manutenzione" }
];

const updated = products.map((p: any) => {
    let suggested = "Altro";
    const title = p.title.toLowerCase();
    
    // Cerchiamo la prima regola che combacia
    for (const rule of rules) {
        if (rule.keywords.some(k => title.includes(k))) {
            suggested = rule.category;
            break;
        }
    }
    
    return { ...p, suggested_category: suggested };
});

fs.writeFileSync("product_category_review.json", JSON.stringify(updated, null, 2));

// Stampiamo un riepilogo
const stats: Record<string, number> = {};
updated.forEach((p: any) => {
    stats[p.suggested_category] = (stats[p.suggested_category] || 0) + 1;
});

console.log("📊 Riepilogo Nuova Categorizzazione:");
console.table(stats);
