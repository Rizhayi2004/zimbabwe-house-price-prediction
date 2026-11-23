import requests
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

url = "https://www.property.co.zw/search"

params = {
    "filterversion": "new",
    "unfilterfeature": "false",
    "type_id": "1",
    "category": "14",
    "14": "14",
    "minprice": "0",
    "maxprice": "100000"
}

r = session.get(url, params=params, timeout=40)
soup = BeautifulSoup(r.text, "html.parser")

cards = soup.select(".ResultCardItem")
links = set()

for card in cards:
    for a in card.select('a[href*="/for-sale/houses-"]'):
        links.add(a["href"])

print("HTTP STATUS:", r.status_code)
print("FINAL URL:", r.url)
print("PAGE TITLE:", soup.title.get_text(strip=True) if soup.title else "None")
print("RESULT CARDS:", len(cards))
print("UNIQUE HOUSE LINKS:", len(links))
print("\nFIRST 10 LINKS:")
for link in list(links)[:10]:
    print(link)

print("\nPAGINATION:")
for a in soup.select("nav.PaginationPortal a[href]"):
    print(a.get_text(" ", strip=True), a["href"])

print("\nPAGE TEXT:")
print(soup.get_text(" ", strip=True)[:1200])
