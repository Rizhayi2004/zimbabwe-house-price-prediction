import requests
from bs4 import BeautifulSoup
from collections import Counter
from urllib.parse import urljoin

base = "https://www.property.co.zw"
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

for page in [1, 50, 100]:
    response = session.get(f"{base}/houses-for-sale?page={page}", timeout=40)
    soup = BeautifulSoup(response.text, "lxml")

    paths = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/for-sale/" in href:
            paths.add(urljoin(base, href).split("?")[0])

    print(f"\n========== PAGE {page} ==========")
    print("Total unique /for-sale/ links:", len(paths))

    prefixes = Counter(
        "/" + path.split("/for-sale/", 1)[1].split("-", 1)[0]
        for path in paths
    )
    print("URL types:", dict(prefixes))

    print("Links not matching houses-:")
    unmatched = [
        path for path in sorted(paths)
        if "/for-sale/houses-" not in path
    ]

    for path in unmatched[:20]:
        print(path)
