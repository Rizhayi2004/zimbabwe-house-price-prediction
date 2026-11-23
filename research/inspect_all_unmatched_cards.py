import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

ranges = [
    (0, 100000),
    (100001, 200000),
    (200001, 300000),
    (300001, 500000),
    (500001, 1000000),
    (1000001, 10000000),
]

seen = set()

for minimum, maximum in ranges:
    for page in range(1, 9):
        response = session.get(
            "https://www.property.co.zw/houses-for-sale",
            params={
                "minprice": minimum,
                "maxprice": maximum,
                "page": page
            },
            timeout=30
        )

        soup = BeautifulSoup(response.text, "html.parser")

        for card in soup.select(".ResultCardItem"):
            for a in card.select("a[href]"):
                href = urljoin(response.url, a["href"])

                if "/for-sale/" not in href:
                    continue

                if "/for-sale/houses-" in href:
                    continue

                if href in seen:
                    continue

                seen.add(href)

                print("\nUNMATCHED LISTING:")
                print("URL:", href)
                print("CARD:", card.get_text(" ", strip=True)[:350])

        time.sleep(1.5)

print("\nTotal unique unmatched URLs:", len(seen))
