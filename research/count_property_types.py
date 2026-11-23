import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

base = "https://www.property.co.zw"
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

houses = set()
townhouses = set()
commercial = set()

for page in range(1, 101):
    response = session.get(f"{base}/houses-for-sale?page={page}", timeout=40)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if re.match(r"^/for-sale/houses-[^/?#]+", href):
            houses.add(urljoin(base, href).split("?")[0])
        elif re.match(r"^/for-sale/townhouses-[^/?#]+", href):
            townhouses.add(urljoin(base, href).split("?")[0])
        elif re.match(r"^/for-sale/commercial-[^/?#]+", href):
            commercial.add(urljoin(base, href).split("?")[0])

    if page % 20 == 0:
        print(f"Scanned {page}/100 pages")

print("\n========== UNIQUE LISTINGS ==========")
print("Houses:", len(houses))
print("Townhouses:", len(townhouses))
print("Commercial listings:", len(commercial))
print("Residential total (houses + townhouses):", len(houses | townhouses))
