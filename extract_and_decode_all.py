
import re
import base64
import urllib.parse
import pandas as pd

def decrypt_netrivals(encoded):
    try:
        # Step 1: URL unquote and B64 decode
        encoded = urllib.parse.unquote(encoded)
        s1 = base64.b64decode(encoded).decode('utf-8', 'ignore')
        
        # Step 2: Remove 4 noise chars at index 12
        if len(s1) > 16:
            clean = s1[:12] + s1[16:]
            # Step 3: Second B64 decode
            # Adding padding to be safe
            missing_padding = len(clean) % 4
            if missing_padding:
                clean += '=' * (4 - missing_padding)
            return base64.b64decode(clean).decode('utf-8', 'ignore')
    except: pass
    return None

def extract_all():
    html_files = ["full_source_rendered.html", "debug_gre_source.html"]
    all_findings = []
    
    for file in html_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Find all jump links
            matches = re.findall(r'store-redirect-url=([^&" >]+)', content)
            # Also find storenames to correlate
            # <a href="...jump?store-redirect-url=...&amp;storename=jollygame"
            correlations = re.findall(r'store-redirect-url=([^&" >]+).*?storename=([^&" >]+)', content, re.DOTALL)
            
            for encoded, storename in correlations:
                decoded = decrypt_netrivals(encoded)
                all_findings.append({
                    "Source_File": file,
                    "StoreName": storename.replace('&amp;', ''),
                    "Decoded_URL": decoded,
                    "Encoded": encoded[:30] + "..."
                })
        except FileNotFoundError:
            print(f"File {file} not found.")

    df = pd.DataFrame(all_findings).drop_duplicates(subset=["StoreName", "Decoded_URL"])
    return df

if __name__ == "__main__":
    results = extract_all()
    print("Decoded Netrivals Links found in HTML files:")
    print(results[["StoreName", "Decoded_URL"]])
    results.to_csv("all_decoded_netrivals_links.csv", index=False)
