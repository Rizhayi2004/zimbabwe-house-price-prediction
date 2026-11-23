import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

url = "https://www.property.co.zw/houses-for-sale"
response = session.get(
    url,
    params={"minprice": 0, "maxprice": 100000, "page": 1},
    timeout=30
)

soup = BeautifulSoup(response.text, "html.parser")

for number, card in enumerate(soup.select(".ResultCardItem"), 1):
    links = []

    for a in card.select("a[href]"):
        href = urljoin(response.url, a["href"])

        if "/for-sale/" in href:
            links.append(href)

    if not any("/for-sale/houses-" in link for link in links):
        print(f"\nCARD {number}")
        print(card.get_text(" ", strip=True)[:250])
        for link in links:
            print(link)
