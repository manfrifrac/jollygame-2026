
import re
import json
import pandas as pd
import base64

def decrypt(encoded):
    try:
        # Step 1: B64 decode
        # Netrivals uses double B64 with noise
        s1 = base64.b64decode(encoded).decode('utf-8', 'ignore')
        # Pattern: remove 4 chars at index 12
        clean = s1[:12] + s1[16:]
        # Decoded clean is the actual URL
        return base64.b64decode(clean + "==").decode('utf-8', 'ignore')
    except Exception as e:
        return None

def extract_from_html():
    with open("full_source_rendered.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Updated regex to handle &amp; and other characters in B64
    links = re.findall(r'store-redirect-url=([^&" \n]+)', content)
    unique_links = list(set(links))
    
    sku_match = re.search(r'Ref\.:?\s*([A-Z0-9]+)', content)
    main_sku = sku_match.group(1) if sku_match else "UNKNOWN"
    
    found = []
    for l in unique_links:
        dec = decrypt(l)
        if dec and "jollygame.it" in dec:
            path = dec.split("jollygame.it")[-1]
            handle = path.split("/")[-1].replace(".html", "")
            found.append({
                "SKU": main_sku,
                "Old_Path": path,
                "New_Handle": handle,
                "Full_URL": dec
            })
            print(f"Found: {handle}")
            
    return pd.DataFrame(found)

if __name__ == "__main__":
    df = extract_from_html()
    if not df.empty:
        df.to_csv("html_extracted_links.csv", index=False)
        print(f"Saved {len(df)} links.")
    else:
        print("No links found.")
