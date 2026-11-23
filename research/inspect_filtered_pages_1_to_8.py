import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
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

for minimum, maximum in ranges:
    print(f"\nPRICE RANGE: ${minimum:,} - ${maximum:,}")

    for page in range(1, 9):
        params = {
            "minprice": minimum,
            "maxprice": maximum,
            "page": page
        }

        try:
            response = session.get(
                "https://www.property.co.zw/houses-for-sale",
                params=params,
                timeout=30
            )

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select(".ResultCardItem")

            ids = set()
            for card in cards:
                for link in card.select("a[href]"):
                    href = urljoin(response.url, link.get("href", ""))
                    if "/for-sale/houses-" in href:
                        ids.add(urlparse(href).path.rstrip("/").split("-")[-1].upper())

            title = soup.title.get_text(strip=True) if soup.title else "No title"

            print(
                f"Page {page}: HTTP {response.status_code} | "
                f"Cards: {len(cards)} | IDs: {len(ids)} | {title}"
            )

        except Exception as error:
            print(f"Page {page}: ERROR: {error}")

        time.sleep(1.5)
