import "@shopify/shopify-api/adapters/node";
import { shopifyApi, LATEST_API_VERSION } from "@shopify/shopify-api";
import dotenv from "dotenv";
import http from "http";
import url from "url";
import fs from "fs";
import path from "path";

dotenv.config();

const shopify = shopifyApi({
  apiKey: process.env.SHOPIFY_API_KEY!,
  apiSecretKey: process.env.SHOPIFY_API_SECRET!,
  scopes: process.env.SCOPES?.split(","),
  hostName: "localhost:3000",
  isEmbeddedApp: false,
  apiVersion: LATEST_API_VERSION,
});

const shop = process.env.SHOP_DOMAIN!;
const port = 3000;

async function startAuth() {
  const server = http.createServer(async (req, res) => {
    const parsedUrl = url.parse(req.url!, true);
    
    if (parsedUrl.pathname === "/auth") {
      // Step 1: Redirect to Shopify for Auth
      const authRoute = await shopify.auth.begin({
        shop,
        callbackPath: "/auth/callback",
        isOnline: false, // Per avere un token permanente (offline)
        rawRequest: req,
        rawResponse: res,
      });
      // Il redirect viene gestito da shopify.auth.begin internamente
    } 
    
    else if (parsedUrl.pathname === "/auth/callback") {
      // Step 2: Receive the code and exchange for token
      try {
        const callbackResponse = await shopify.auth.callback({
          rawRequest: req,
          rawResponse: res,
        });

        const session = callbackResponse.session;
        console.log("\n✅ Token generato con successo!");
        console.log(`📦 Token: ${session.accessToken}`);

        // Salva il token nel .env
        const envPath = path.resolve(".env");
        let envContent = fs.readFileSync(envPath, "utf-8");
        
        if (envContent.includes("SHOPIFY_ACCESS_TOKEN=")) {
          envContent = envContent.replace(/SHOPIFY_ACCESS_TOKEN=.*/, `SHOPIFY_ACCESS_TOKEN=${session.accessToken}`);
        } else {
          envContent += `\nSHOPIFY_ACCESS_TOKEN=${session.accessToken}`;
        }
        
        fs.writeFileSync(envPath, envContent);
        console.log("💾 Token salvato in .env\n");

        res.end("Autenticazione completata! Torna alla console.");
        process.exit(0);
      } catch (e) {
        console.error("❌ Errore durante il callback:", e);
        res.end("Errore durante l'autenticazione.");
      }
    }
  });

  server.listen(port, () => {
    console.log(`\n🚀 Server di autenticazione in esecuzione su http://localhost:${port}`);
    console.log(`👉 Visita questo link per iniziare: http://localhost:${port}/auth`);
    console.log(`(Assicurati che http://localhost:3000/auth/callback sia nei 'Redirect URLs' della tua App nel Partner Dashboard)\n`);
  });
}

startAuth().catch(console.error);
