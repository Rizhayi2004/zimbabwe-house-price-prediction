
import requests
from bs4 import BeautifulSoup
import json

URL = "https://www.property.co.zw/for-sale/houses-fac253758"

HEADERS = {
    "User-Agent": "Academic research project - Zimbabwe House Price Prediction"
}

response = requests.get(URL, headers=HEADERS, timeout=30)

print("HTTP Status:", response.status_code)
response.raise_for_status()

soup = BeautifulSoup(response.text, "lxml")

print("\nPAGE TITLE:")
print(soup.title.get_text(strip=True) if soup.title else "Not found")

print("\nPAGE TEXT:")
print(soup.get_text(" ", strip=True)[:10000])

print("\nJSON-LD STRUCTURED DATA:")
for script in soup.find_all("script", type="application/ld+json"):
    try:
        data = json.loads(script.string or script.get_text())
        print(json.dumps(data, indent=2)[:5000])
    except (json.JSONDecodeError, TypeError):
        print("Could not parse JSON-LD")

print("\nIMAGE URLS:")
for img in soup.find_all("img"):
    src = img.get("src") or img.get("data-src")
    if src:
        print(src)
