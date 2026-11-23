import requests
from bs4 import BeautifulSoup

url = "https://www.property.co.zw/houses-for-sale?page=1"
response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=40
)

soup = BeautifulSoup(response.text, "lxml")
form = soup.find("form", action="/search")

print("FORM ATTRIBUTES:")
print(form.attrs)

print("\nLOCATION SELECT MARKUP:")
for name in ["Locations", "site_ids", "neighborhood_ids", "development_ids"]:
    element = form.find("select", {"name": name})
    if element:
        print(f"\n--- {name} ---")
        print(element.prettify()[:5000])

print("\nHIDDEN INPUTS:")
for field in form.find_all("input", {"type": "hidden"}):
    print(field.get("name"), "=", field.get("value"))

print("\nRELATED JAVASCRIPT FILES:")
for script in soup.find_all("script", src=True):
    src = script.get("src", "")
    if any(word in src.lower() for word in ["portal", "search", "filter", "location"]):
        print(src)

print("\nSEARCH FORM BUTTONS:")
for button in form.find_all("button"):
    print(button.attrs, button.get_text(" ", strip=True))
