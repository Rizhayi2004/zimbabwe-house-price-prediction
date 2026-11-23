import requests
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

base = "https://www.property.co.zw"
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

all_urls = set()
failed_pages = []
empty_pages = []

for page in range(1, 101):
    success = False

    for attempt in range(3):
        try:
            url = f"{base}/houses-for-sale?page={page}"
            response = session.get(url, timeout=40)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            links = {
                urljoin(base, a["href"])
                for a in soup.find_all("a", href=True)
                if re.match(r"^/for-sale/houses-[^/?#]+", a["href"])
            }

            if not links:
                empty_pages.append(page)
            else:
                all_urls.update(links)

            success = True
            break

        except Exception as error:
            if attempt == 2:
                failed_pages.append((page, str(error)))
            else:
                time.sleep(2)

    if page % 10 == 0:
        print(f"Checked page {page}/100 | Unique URLs so far: {len(all_urls)}")

print("\n========== RESULTS ==========")
print("Unique listing URLs across pages 1-100:", len(all_urls))
print("Empty pages:", empty_pages)
print("Failed pages:", failed_pages)
