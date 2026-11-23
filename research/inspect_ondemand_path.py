import requests
import re
from bs4 import BeautifulSoup

base = "https://www.property.co.zw"
url = base + "/houses-for-sale?page=1"

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=40
)

html = response.text
soup = BeautifulSoup(html, "lxml")

print("PAGE SCRIPT REFERENCES:")
for script in soup.find_all("script", src=True):
    print(script.get("src"))

print("\nONDEMAND_PATH REFERENCES IN PAGE HTML:")
for match in re.finditer(r"ONDEMAND_PATH", html):
    print(html[max(0, match.start()-250):match.end()+300])

print("\nONDEMAND_PATH REFERENCES IN PORTAL JS:")
js_url = base + "/content/overhaul/js/portal.min.js?v=3.1.2.13579"
js = requests.get(
    js_url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=40
).text

for match in re.finditer(r"ONDEMAND_PATH", js):
    print(js[max(0, match.start()-300):match.end()+300])
