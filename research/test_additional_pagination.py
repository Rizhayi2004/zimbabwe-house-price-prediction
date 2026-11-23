
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path("src").resolve()))

import collect_additional_listings as collector

http = collector.scraper.session

tests = [
    (0, 100000, 1),
    (0, 100000, 2),
    (0, 100000, 33),
    (100001, 200000, 2),
]

for low, high, page in tests:
    print("\n" + "=" * 55)
    print(f"Testing ${low:,} - ${high:,}, page {page}")

    try:
        soup = collector.fetch_listing_page(
            http, low, high, page
        )

        print("Page title:", soup.title.get_text(strip=True))
        print("Final URL:", http.cookies.get_dict())
        urls = collector.extract_house_urls(soup)
        print("House URLs found:", len(urls))

        for url in sorted(urls)[:3]:
            print(url)

    except Exception as exc:
        print("TEST FAILED:", repr(exc))
