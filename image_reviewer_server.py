import http.server
import socketserver
import json
import os
import pandas as pd
import urllib.parse
from urllib.parse import urlparse, parse_qs

PORT = 8000
IMAGE_RESULTS_FILE = 'gre_missing_images_final.json'
APPROVED_IMAGES_FILE = 'immagini_approvate.json'
MISSING_PRODUCTS_CSV = 'prodotti_gre_mancanti.csv'

class ImageReviewHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # Load Data
            with open(IMAGE_RESULTS_FILE, 'r') as f:
                scraped_data = json.load(f)
            
            df = pd.read_csv(MISSING_PRODUCTS_CSV)
            df = df[df['sku'] != 'ARTICOLO']
            
            # Load Approved
            approved_skus = set()
            if os.path.exists(APPROVED_IMAGES_FILE):
                with open(APPROVED_IMAGES_FILE, 'r') as f:
                    approved_data = json.load(f)
                    approved_skus = set(approved_data.keys())

            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Gre Image Reviewer</title>
                <style>
                    body { font-family: sans-serif; padding: 20px; background: #f4f4f9; }
                    .product-card { background: white; margin-bottom: 30px; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                    .product-card.hidden { display: none; }
                    .image-grid { display: flex; flex-wrap: wrap; gap: 15px; margin-top: 15px; }
                    .image-item { border: 2px solid #eee; padding: 5px; border-radius: 5px; text-align: center; max-width: 250px; }
                    .image-item img { max-width: 100%; max-height: 200px; display: block; margin-bottom: 10px; border-radius: 3px; }
                    .btn { cursor: pointer; padding: 8px 12px; border: none; border-radius: 4px; font-weight: bold; }
                    .btn-select { background: #28a745; color: white; width: 100%; }
                    .btn-reject { background: #dc3545; color: white; margin-top: 10px; }
                    h2 { margin: 0; color: #333; }
                    .sku { color: #666; font-family: monospace; font-size: 1.1em; }
                    .stats { position: sticky; top: 0; background: #333; color: white; padding: 10px; border-radius: 5px; margin-bottom: 20px; z-index: 100; }
                </style>
            </head>
            <body>
                <div class="stats">
                    Approvati: <span id="count-approved">0</span> | Rimanenti: <span id="count-remaining">0</span>
                </div>
                <h1>Review Immagini Gre</h1>
            """
            
            remaining_count = 0
            for _, row in df.iterrows():
                sku = str(row['sku']).strip().upper()
                if sku in approved_skus: continue
                
                imgs = scraped_data.get(sku, [])
                if not imgs: continue # Skip if no images found yet
                
                remaining_count += 1
                html += f"""
                <div class="product-card" id="card-{sku}">
                    <h2>{row['title']}</h2>
                    <div class="sku">SKU: {sku}</div>
                    <div class="image-grid">
                """
                for img_url in imgs:
                    html += f"""
                        <div class="image-item">
                            <img src="{img_url}" onerror="this.src='https://placehold.co/200x200?text=Error+Loading'">
                            <button class="btn btn-select" onclick="selectImage('{sku}', '{img_url}')">✅ Seleziona</button>
                        </div>
                    """
                html += f"""
                    </div>
                    <button class="btn btn-reject" onclick="selectImage('{sku}', 'REJECTED')">❌ Nessuna immagine va bene</button>
                </div>
                """
            
            html += f"""
                <script>
                    let remaining = {remaining_count};
                    let approved = {len(approved_skus)};
                    
                    document.getElementById('count-remaining').innerText = remaining;
                    document.getElementById('count-approved').innerText = approved;

                    function selectImage(sku, url) {{
                        fetch('/save', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                            body: 'sku=' + encodeURIComponent(sku) + '&url=' + encodeURIComponent(url)
                        }}).then(res => {{
                            if (res.ok) {{
                                document.getElementById('card-' + sku).classList.add('hidden');
                                remaining--;
                                approved++;
                                document.getElementById('count-remaining').innerText = remaining;
                                document.getElementById('count-approved').innerText = approved;
                                if (remaining === 0) alert('Hai finito tutti i prodotti con immagini!');
                            }}
                        }});
                    }}
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            return super().do_GET()

    def do_POST(self):
        if self.path == '/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            
            sku = params.get('sku', [''])[0]
            url = params.get('url', [''])[0]
            
            if sku:
                approved_data = {}
                if os.path.exists(APPROVED_IMAGES_FILE):
                    with open(APPROVED_IMAGES_FILE, 'r') as f:
                        approved_data = json.load(f)
                
                approved_data[sku] = url
                
                with open(APPROVED_IMAGES_FILE, 'w') as f:
                    json.dump(approved_data, f, indent=4)
                
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Saved")
            else:
                self.send_response(400)
                self.end_headers()

with socketserver.TCPServer(("", PORT), ImageReviewHandler) as httpd:
    print(f"Server avviato su http://localhost:{PORT}")
    print("Vai nel tuo browser per iniziare il controllo delle immagini.")
    print("Premi Ctrl+C per fermare il server quando hai finito.")
    httpd.serve_forever()
