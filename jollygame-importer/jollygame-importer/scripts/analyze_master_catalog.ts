import fs from "fs";

const catalog = JSON.parse(fs.readFileSync("master_catalog_dump.json", "utf8"));

const finalMapping: any[] = [];

for (const p of catalog) {
    const title = p.title.toLowerCase();
    const vendor = (p.vendor || "").toLowerCase();
    let targetCategory = "ALTRO";
    let targetSub = "Generico";

    // 1. PISCINE
    const poolKeywords = ["piscina", "easy set", "prisma", "ultra xtr", "graphite", "sicilia", "pacific", "fidji", "bora bora", "haiti", "atlantis", "mauritius", "varadero", "granada", "lili", "grenade", "marbella", "vermela", "city", "mint", "avantgarde", "dolcevita", "bluespring", "ninfea", "pop!", "classic", "playa", "professional", "musa", "piscine intex", "antea"];
    const poolForbidden = ["telo", "copertura", "copri", "liner", "robot", "pulitore", "spazzola", "filtro", "pompa", "motore", "raccordo", "tubo", "adesivo", "tester", "analisi", "cloro", "bromo", "svernante", "anticalcare", "kit di pulizia", "aspiratore", "manuale", "ricambio", "pezzo", "guarnizione", "vite", "bullone", "tappo", "regolatore", "plug", "casetta", "proiettore", "led", "lampada", "scaletta", "doccia", "bicicletta", "spugne", "cartuccia", "skimmer", "manico", "avvolgitore", "protezione", "barriera", "testa aspirante", "chlorinanti"];

    if (poolKeywords.some(k => title.includes(k)) && !poolForbidden.some(k => title.includes(k))) {
        targetCategory = "PISCINE";
        if (vendor === 'piscine laghetto') targetSub = "Laghetto (Luxury)";
        else if (title.includes("acciaio") || ["sicilia", "pacific", "fidji", "bora bora", "haiti", "atlantis", "steel", "mauritius", "varadero", "granada"].some(k => title.includes(k))) targetSub = "Acciaio";
        else if (title.includes("legno") || ["lili", "grenade", "marbella", "vermela", "city", "mint"].some(k => title.includes(k))) targetSub = "Legno";
        else if (title.includes("composito") || title.includes("composite") || title.includes("avantgarde")) targetSub = "Composito";
        else targetSub = "Fuori Terra (Intex/Bestway/Gre)";
    }
    // 2. PULITORI
    else if (["robot", "pulitore", "aspiratore", "spazzola", "retino", "vac", "sweepy", "voyager", "cnx", "alpha", "vortex", "testa aspirante", "aspirafango", "xa ", "ra ", "oa ", "swy", "ov ", "ot ", "gt ", "rt ", "rf ", "of ", "gv ", "re ", "trx", "e30", "op ", "px25"].some(k => title.includes(k))) {
        targetCategory = "PULITORI";
        if (title.includes("robot") || title.includes("elettrico") || ["cnx", "voyager", "alpha", "ra ", "oa ", "swy", "ov ", "xa ", "rf ", "of ", "re ", "trx", "e30", "op "].some(k => title.includes(k))) targetSub = "Elettrici (Robot)";
        else targetSub = "Manuali/Idraulici";
    }
    // 3. TRATTAMENTO ACQUA
    else if (["cloro", "dicloro", "bromo", "antialghe", "flocculante", "svernante", "alcalinità", "ph", "regolatore", "analizzatore", "tester", "trattamento", "sale", "gel", "ossigeno", "clorinatore", "disinfezione", "analizzatore", "blue fit", "blue connect", "exo", "ei2", "eisalt", "expert", "chlor expert", "dual link", "link", "chlorinanti"].some(k => title.includes(k))) {
        targetCategory = "TRATTAMENTO";
    }
    // 4. FILTRAGGIO
    else if (["filtro", "depuratore", "monoblocco", "sabbia", "cartuccia", "pompa", "skimmer", "raccordo", "tubo", "manicotto", "bocchetta", "collettore", "valvola", "manometro", "flopro", "iqpump", "crystal clear", " cs"].some(k => title.includes(k))) {
        if (!title.includes("calore")) {
            targetCategory = "FILTRAGGIO";
            if (title.includes("pompa") || title.includes("motore") || title.includes("flopro")) targetSub = "Pompe";
            else targetSub = "Filtri e Idraulica";
        } else {
            targetCategory = "RISCALDAMENTO";
        }
    }
    // 5. RISCALDAMENTO
    else if (["pompa di calore", "riscaldamento", "z250", "z350", "z400", "z550", "z650", "z950", "inverter", "solare", "sirocco", "heat line", "cae", "dt 850"].some(k => title.includes(k))) {
        targetCategory = "RISCALDAMENTO";
    }
    // 6. ACCESSORI
    else if (["copertura", "telo", "copri", "liner", "riparazione", "adesivo", "luce", "led", "lampada", "proiettore", "scaletta", "doccia", "bicicletta", "tappeto", "casetta", "protezione", "barriera", "manico", "avvolgitore", "termometro", "erogatore", "plug", "spugne", "estensore wifi", "freedom"].some(k => title.includes(k))) {
        targetCategory = "ACCESSORI";
        if (title.includes("copertura") || title.includes("telo") || title.includes("copri")) targetSub = "Coperture";
        else if (title.includes("liner") || title.includes("riparazione")) targetSub = "Liner";
        else if (title.includes("scaletta")) targetSub = "Scalette";
        else if (title.includes("doccia")) targetSub = "Docce";
        else if (title.includes("luce") || title.includes("led") || title.includes("lampada")) targetSub = "Illuminazione";
        else targetSub = "Accessori Vari";
    }

    finalMapping.push({
        id: p.id,
        title: p.title,
        old_tags: p.tags,
        new_category: targetCategory,
        new_sub: targetSub
    });
}

fs.writeFileSync("target_categorization.json", JSON.stringify(finalMapping, null, 2));
console.log("✅ Analisi finale salvata.");
