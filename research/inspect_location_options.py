import requests
from bs4 import BeautifulSoup

url = "https://www.property.co.zw/houses-for-sale?page=1"
soup = BeautifulSoup(
    requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=40).text,
    "lxml"
)

form = soup.find("form", action="/search")

for select in form.find_all("select"):
    print("\n" + "=" * 50)
    print("SELECT:", select.get("name"), "| ID:", select.get("id"))

    for option in select.find_all("option"):
        value = option.get("value", "")
        label = option.get_text(" ", strip=True)
        print(f"{value} | {label}")

print("\n" + "=" * 50)
print("LOCATION CHECKBOXES")

for checkbox in form.find_all("input", {"type": "checkbox"}):
    parent = checkbox.parent
    label = parent.get_text(" ", strip=True) if parent else ""
    print(
        "ID:", checkbox.get("id"),
        "| NAME:", checkbox.get("name"),
        "| VALUE:", checkbox.get("value"),
        "| LABEL:", label[:120]
    )
