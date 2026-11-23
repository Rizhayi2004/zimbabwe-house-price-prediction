import requests
import re
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

pages = [1, 50, 85, 90, 95, 97, 98, 99, 100, 101, 120, 130, 132, 140]

for page in pages:
    try:
        url = f"https://www.property.co.zw/houses-for-sale?page={page}"
        response = session.get(url, timeout=40)
        soup = BeautifulSoup(response.text, "lxml")

        links = {
            a["href"]
            for a in soup.find_all("a", href=True)
            if re.match(r"^/for-sale/houses-[^/?#]+", a["href"])
        }

        match = re.search(
            r"\d+\s*-\s*\d+\s+of\s+[\d,]+",
            soup.get_text(" ", strip=True)
        )

        listing_range = match.group(0) if match else "not shown"

        print(
            f"Page {page}: HTTP {response.status_code} | "
            f"Listings {listing_range} | House links {len(links)}"
        )

    except Exception as error:
        print(f"Page {page}: ERROR {error}")
