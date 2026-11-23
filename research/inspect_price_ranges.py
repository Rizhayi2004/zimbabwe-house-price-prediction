import requests
from bs4 import BeautifulSoup
import re

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

ranges = [
    (0, 100000),
    (100001, 200000),
    (200001, 300000),
    (300001, 500000),
    (500001, 1000000),
    (1000001, 10000000)
]

for low, high in ranges:
    params = {
        "filterversion": "new",
        "unfilterfeature": "false",
        "type_id": "1",
        "category": "14",
        "14": "14",
        "minprice": low if low > 0 else "",
        "maxprice": high
    }

    r = session.get(
        "https://www.property.co.zw/search",
        params=params,
        timeout=40
    )

    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    match = re.search(r"([\d,]+)\s+listings", title, re.I)

    print(
        f"${low:,}-${high:,} | "
        f"{match.group(1) if match else title} | "
        f"First-page cards: {len(soup.select('.ResultCardItem'))} | "
        f"HTTP: {r.status_code}"
    )
