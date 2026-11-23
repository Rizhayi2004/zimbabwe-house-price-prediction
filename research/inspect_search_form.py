import requests
from bs4 import BeautifulSoup

url = "https://www.property.co.zw/houses-for-sale?page=1"
s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0"})

r = s.get(url, timeout=40)
soup = BeautifulSoup(r.text, "html.parser")
form = soup.find("form", id="searchResultForm")

print("FORM ACTION:", form.get("action"))
print("FORM METHOD:", form.get("method", "GET (default)"))

print("\nFORM INPUTS:")
for x in form.find_all(["input", "select", "button"]):
    print({
        "tag": x.name,
        "type": x.get("type"),
        "name": x.get("name"),
        "value": x.get("value"),
        "id": x.get("id"),
        "selected": [
            o.get("value") for o in x.find_all("option", selected=True)
        ] if x.name == "select" else None
    })
