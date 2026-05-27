import dotenv from "dotenv";
import http from "http";
import url from "url";
import fs from "fs";
import path from "path";

dotenv.config();

const apiKey = process.env.SHOPIFY_API_KEY!;
const apiSecret = process.env.SHOPIFY_API_SECRET!;
const shop = process.env.SHOP_DOMAIN!;
const port = 3000;
const redirectUri = `http://localhost:${port}/auth/callback`;

async function startAuth() {
  const server = http.createServer(async (req, res) => {
    const parsedUrl = url.parse(req.url!, true);
    
    if (parsedUrl.pathname === "/auth") {
      const scopes = process.env.SCOPES || "write_products,read_products,write_content,read_content";
      const authUrl = `https://${shop}/admin/oauth/authorize?client_id=${apiKey}&scope=${scopes}&redirect_uri=${redirectUri}&state=12345`;
      
      res.writeHead(302, { Location: authUrl });
      res.end();
    } 
    
    else if (parsedUrl.pathname === "/auth/callback") {
      const code = parsedUrl.query.code as string;
      
      if (!code) {
        res.end("Errore: Codice non ricevuto.");
        return;
      }

      console.log(`\n📥 Codice ricevuto: ${code}`);
      console.log("⏳ Scambio del codice con l'Access Token...");

      try {
        const response = await fetch(`https://${shop}/admin/oauth/access_token`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            client_id: apiKey,
            client_secret: apiSecret,
            code: code,
          }),
        });

        const text = await response.text();
        let data: any;
        try {
            data = JSON.parse(text);
        } catch (e) {
            console.error("❌ Risposta non JSON da Shopify:", text);
            res.end(`Errore: Shopify ha risposto con dati non validi. Controlla la console.`);
            return;
        }

        if (data.access_token) {
          console.log("\n✅ Token generato con successo!");
          console.log(`📦 Token: ${data.access_token}`);

          const envPath = path.resolve(".env");
          let envContent = fs.readFileSync(envPath, "utf-8");
          
          if (envContent.includes("SHOPIFY_ACCESS_TOKEN=")) {
            envContent = envContent.replace(/SHOPIFY_ACCESS_TOKEN=.*/, `SHOPIFY_ACCESS_TOKEN=${data.access_token}`);
          } else {
            envContent += `\nSHOPIFY_ACCESS_TOKEN=${data.access_token}`;
          }
          
          fs.writeFileSync(envPath, envContent);
          console.log("💾 Token salvato in .env\n");

          res.end("Autenticazione completata! Il token e' stato salvato nel file .env.");
          process.exit(0);
        } else {
          console.error("❌ Errore nello scambio del token:", data);
          res.end(`Errore: ${data.error_description || data.error || JSON.stringify(data)}`);
        }
      } catch (e) {
        console.error("❌ Errore durante la richiesta:", e);
        res.end("Errore durante la richiesta del token.");
      }
    }
  });

  server.listen(port, () => {
    console.log(`\n🚀 Server di autenticazione manuale in esecuzione su http://localhost:${port}`);
    console.log(`👉 Visita questo link per iniziare: http://localhost:${port}/auth\n`);
  });
}

startAuth().catch(console.error);
