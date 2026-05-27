import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";
import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";

if (!SHOP_DOMAIN || !ACCESS_TOKEN) {
  console.error("Missing SHOP_DOMAIN or SHOPIFY_ACCESS_TOKEN in .env");
  process.exit(1);
}

const csvFilePath = path.resolve("../../zodiac_enriched_data.csv");

const mutation = `
mutation productCreate($input: ProductInput!) {
  productCreate(input: $input) {
    product {
      id
      title
    }
    userErrors {
      field
      message
    }
  }
}
`;

async function importProducts() {
  const content = fs.readFileSync(csvFilePath, "utf-8");
  const records = parse(content, {
    columns: true,
    skip_empty_lines: true,
  });

  console.log(`Found ${records.length} records to import. Testing first 2.`);

  for (const record of records.slice(0, 2)) {
    const title = record.Titolo || "Senza Titolo";
    const descriptionHtml = record.Descrizione_HTML || record.Sottotitolo || "";
    const tags = record.Tags ? record.Tags.split(",").map((t: string) => t.trim()) : [];
    const images = record.Immagini ? record.Immagini.split(",").map((src: string) => ({ src: src.trim() })) : [];
    
    // Pulizia prezzo
    let price = "0.00";
    if (record.Prezzo) {
      price = record.Prezzo.replace(/[^\d.,]/g, "").replace(",", ".");
      if (!price || isNaN(parseFloat(price))) price = "0.00";
    }

    const input = {
      title,
      descriptionHtml,
      vendor: "Zodiac",
      tags,
      images,
      variants: [
        {
          price,
          sku: record.URL.split("/").pop() || undefined,
        }
      ]
    };

    console.log(`Importing: ${title}...`);

    try {
      const response = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Shopify-Access-Token": ACCESS_TOKEN,
        },
        body: JSON.stringify({
          query: mutation,
          variables: { input },
        }),
      });

      const result: any = await response.json();

      if (result.errors) {
        console.error(`  [ERROR GraphQL]:`, result.errors);
      } else if (result.data?.productCreate?.userErrors?.length > 0) {
        console.error(`  [ERROR User]:`, result.data.productCreate.userErrors);
      } else {
        console.log(`  [OK] Created ID: ${result.data.productCreate.product.id}`);
      }
    } catch (error) {
      console.error(`  [ERROR Fetch]:`, error);
    }

    // Rate limiting base
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}

importProducts().catch(console.error);
