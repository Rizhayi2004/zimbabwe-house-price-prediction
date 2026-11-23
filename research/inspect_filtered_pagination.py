import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

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

    response = session.get(
        "https://www.property.co.zw/houses-for-sale",
        params={"minprice": minimum, "maxprice": maximum, "page": 1},
        timeout=30
    )

    soup = BeautifulSoup(response.text, "html.parser")
    pages = set()

    for link in soup.select("a[href]"):
        href = link.get("href", "")
        if "page=" in href:
            parsed = urlparse(href)
            page = parse_qs(parsed.query).get("page", [])
            if page and page[0].isdigit():
                pages.add(int(page[0]))

    print("Advertised page numbers:", sorted(pages))
    print("Last advertised page:", max(pages) if pages else "Not found")
