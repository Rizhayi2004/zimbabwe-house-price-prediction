
import requests
import json
import re
from bs4 import BeautifulSoup

URL = "https://www.property.co.zw/for-sale/houses-fac253758"

HEADERS = {
    "User-Agent": "Academic research project - Zimbabwe House Price Prediction"
}

response = requests.get(URL, headers=HEADERS, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "lxml")

listing = None

for script in soup.find_all("script", type="application/ld+json"):
    try:
        data = json.loads(script.string or script.get_text())
    except (json.JSONDecodeError, TypeError):
        continue

    if isinstance(data, dict) and data.get("@type") == "RealEstateListing":
        listing = data
        break

if not listing:
    print("RealEstateListing structured data not found.")
    raise SystemExit

about = listing.get("about", {})
offer = listing.get("offers", {})
address = about.get("address", {})
floor = about.get("floorSize", {})

page_text = soup.get_text(" ", strip=True)

land_match = re.search(
    r"([\d,]+(?:\.\d+)?)\s*m²\s+stand",
    page_text,
    re.IGNORECASE
)

breadcrumbs = []

for script in soup.find_all("script", type="application/ld+json"):
    try:
        data = json.loads(script.string or script.get_text())
    except (json.JSONDecodeError, TypeError):
        continue

    if isinstance(data, dict) and data.get("@type") == "BreadcrumbList":
        breadcrumbs = [
            item.get("name")
            for item in data.get("itemListElement", [])
        ]
        break

print("\nEXTRACTED LISTING DATA")
print("----------------------")
print("Listing ID:", listing.get("identifier"))
print("Title:", listing.get("name"))
print("Price:", offer.get("price"))
print("Currency:", offer.get("priceCurrency"))
print("City breadcrumb:", breadcrumbs[1] if len(breadcrumbs) > 1 else None)
print("Suburb:", address.get("addressLocality"))
print("Region:", address.get("addressRegion"))
print("Bedrooms:", about.get("numberOfBedrooms"))
print("Bathrooms:", about.get("numberOfBathroomsTotal"))
print("Floor size:", floor.get("value"))
print("Land size:", land_match.group(1) if land_match else None)
print("Description:", listing.get("description"))
print("Number of photos:", len(listing.get("image", [])))
print("Listing URL:", listing.get("url"))
