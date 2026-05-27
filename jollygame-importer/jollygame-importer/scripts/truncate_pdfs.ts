import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";
import { stringify } from "csv-stringify/sync";

const csvPath = path.resolve("../../zodiac_enriched_data.csv");
const records = parse(fs.readFileSync(csvPath, "utf-8"), { columns: true, skip_empty_lines: true });

const updatedRecords = records.map(record => {
    if (['eXPERT pH', 'Freedom Lite'].includes(record.Titolo.trim())) {
        console.log(`✂️ Troncando PDF per: ${record.Titolo}`);
        // Keep only the first document to stay well under 255 chars
        const docs = record.PDF_Documents.split(';');
        record.PDF_Documents = docs[0].trim();
    }
    return record;
});

fs.writeFileSync(csvPath, stringify(updatedRecords, { header: true }));
console.log("✅ CSV aggiornato con PDF troncati.");
