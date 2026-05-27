
import re
import json
import pandas as pd

def extract_from_html():
    with open("full_source_rendered.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Looking for store-redirect-url in netrivals links
    # Then I'll decode them manually since I know the pattern
    import base64
    def decrypt(encoded):
        try:
            s1 = base64.b64decode(encoded).decode('utf-8', 'ignore')
            # remove 4 chars at index 12
            clean = s1[:12] + s1[16:]
            # The pattern for Sumatra was that s1 already looks like aHR0cHM6Ly93...
            # And after cleaning it's a valid B64 of the URL
            return base64.b64decode(clean + "==").decode('utf-8', 'ignore')
        except: return None

    links = re.findall(r'store-redirect-url=([^&" \n]+)', content)
    unique_links = list(set(links))
    
    found = []
    for l in unique_links:
        dec = decrypt(l)
        if dec and "jollygame.it" in dec:
            path = dec.split("jollygame.it")[-1]
            handle = path.split("/")[-1].replace(".html", "")
            found.append({
                "URL": dec,
                "Path": path,
                "Handle": handle
            })
    
    # We need to map these to SKUs. In the HTML, Sumatra Ovale is the main product.
    # Ref.: KPEOV5027
    sku_match = re.search(r'Ref\.:?\s*([A-Z0-9]+)', content)
    main_sku = sku_match.group(1) if sku_match else "UNKNOWN"
    
    results = []
    for f in found:
        # Most likely these links correspond to the variants or the main product
        # For now, let's assume they are for the main SKU or contains the SKU in handle
        results.append({
            "SKU": main_sku, 
            "Old_Path": f['Path'],
            "New_Handle": f['Handle']
        })
        
    return pd.DataFrame(results)

if __name__ == "__main__":
    df = extract_from_html()
    print(df)
    df.to_csv("html_extracted_links.csv", index=False)
