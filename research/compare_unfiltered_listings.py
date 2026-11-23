import re
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.property.co.zw"
AUDIT_FILE = Path("data/raw/additional_house_listing_urls.txt")
OUTPUT_FILE = Path("data/raw/unfiltered_missing_listing_urls.txt")

def extract_ids(urls):
    ids = set()
    for url in urls:
        match = re.search(r"/for-sale/houses-([^/?#]+)", url)
        if match:
            ids.add(match.group(1).lower())
    return ids

existing_urls = AUDIT_FILE.read_text(encoding="utf-8").splitlines()
existing_ids = extract_ids(existing_urls)

print("Existing saved URLs:", len(existing_urls))
print("Existing unique IDs:", len(existing_ids))
print("\nScanning unfiltered pages 1–100...")

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

all_urls = set()

for page in range(1, 101):
    url = f"{BASE_URL}/houses-for-sale?page={page}"

    try:
        response = session.get(url, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        page_urls = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            match = re.search(r"/for-sale/houses-([^/?#]+)", href)

            if match:
                listing_id = match.group(1).lower()
                page_urls.add(
                    f"{BASE_URL}/for-sale/houses-{listing_id}"
                )

        all_urls.update(page_urls)

        print(
            f"Page {page:3}: HTTP {response.status_code} | "
            f"{len(page_urls)} unique listings | "
            f"{len(all_urls)} cumulative"
        )

    except Exception as error:
        print(f"Page {page:3}: ERROR - {error}")

    time.sleep(1.5)

unfiltered_ids = extract_ids(all_urls)

missing_ids = unfiltered_ids - existing_ids

missing_urls = sorted(
    f"{BASE_URL}/for-sale/houses-{listing_id}"
    for listing_id in missing_ids
)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE.write_text(
    "\n".join(missing_urls),
    encoding="utf-8"
)

print("\n" + "=" * 55)
print("COMPARISON RESULTS")
print("=" * 55)
print("Unique unfiltered listing IDs:", len(unfiltered_ids))
print("Already in existing URL audit:", len(unfiltered_ids & existing_ids))
print("New unique listing IDs:", len(missing_ids))
print("Saved new URLs to:", OUTPUT_FILE)

print("\nFirst 10 new URLs:")
for url in missing_urls[:10]:
    print(url)
