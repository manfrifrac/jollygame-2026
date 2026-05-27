
import pandas as pd
import re
import os

def extract_all_old_links():
    csv_path = 'mapping_completo_PER_LAVORO_MANUALE.csv'
    df = pd.read_csv(csv_path)
    
    found_links = []
    
    for index, row in df.iterrows():
        sku = str(row['SKU']).strip().upper()
        
        # Check all columns for a jollygame.it/...html link
        for col in df.columns:
            val = str(row[col])
            if "jollygame.it" in val and ".html" in val:
                # Extract the path from the URL
                # Example: https://jollygame.it/category/path.html -> /category/path.html
                match = re.search(r'jollygame\.it(/.*\.html)', val)
                if match:
                    path = match.group(1)
                    handle = path.split("/")[-1].replace(".html", "")
                    found_links.append({
                        "SKU": sku,
                        "Old_Path": path,
                        "New_Handle": handle
                    })
                    break # Stop at first found link for this SKU
                    
    results_df = pd.DataFrame(found_links).drop_duplicates(subset=['SKU'])
    results_df.to_csv("discovered_old_links.csv", index=False)
    print(f"Discovered {len(results_df)} old links in CSV.")
    return results_df

if __name__ == "__main__":
    extract_all_old_links()
