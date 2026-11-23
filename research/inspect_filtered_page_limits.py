import requests
from bs4 import BeautifulSoup

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

    for page in [1, 99, 100, 101]:
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
            title = soup.title.get_text(strip=True) if soup.title else "No title"

            print(
                f"Page {page}: HTTP {response.status_code} | "
                f"Cards: {len(cards)} | Title: {title}"
            )

        except Exception as error:
            print(f"Page {page}: ERROR: {error}")

    import time
    time.sleep(1.5)
