import urllib.request

url = "https://pro.fluidra.com/it_it/catalogsearch/result/?q=R0516700"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        with open("fluidra_search.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Scaricato")
except Exception as e:
    print(e)
