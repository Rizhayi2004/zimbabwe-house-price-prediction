import requests
import re
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

pages = [1, 2, 50, 100, 101, 120, 130, 140, 150]

for page in pages:
    url = f"https://www.property.co.zw/houses-for-sale?page={page}"

    try:
        response = session.get(url, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.search(r"/for-sale/houses-[^/?#]+", href):
                full_url = requests.compat.urljoin(url, href)
                if full_url not in links:
                    links.append(full_url)

        print(f"\nPAGE {page}")
        print("Status:", response.status_code)
        print("Title:", soup.title.get_text(strip=True) if soup.title else "No title")
        print("Unique listing links:", len(links))
        print("First listing:", links[0] if links else "None")
        print("Last listing:", links[-1] if links else "None")

    except Exception as error:
        print(f"\nPAGE {page} ERROR:", error)
