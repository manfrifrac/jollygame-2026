import sys
import base64

with open("debug_fluidra_login.html", "r", encoding="utf-8") as f:
    html = f.read()
    
print("Title:", html[html.find('<title>'):html.find('</title>')+8])
if "username" in html:
    print("Username field exists in HTML")
else:
    print("No username field in HTML")
