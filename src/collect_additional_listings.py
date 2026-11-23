
"""
Collect additional Zimbabwe house listings from Property.co.zw.

Uses direct /houses-for-sale pagination.
Deduplicates listing IDs across price ranges.
Backs up the existing CSV before appending.
Stops at 2,400 unique listing IDs.
"""

import csv
import math
import random
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import (
    urljoin,
    urldefrag,
    urlparse,
    parse_qs,
)

import requests
from bs4 import BeautifulSoup

import scrape_listings as scraper


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "data" / "raw" / "house_listings.csv"
URL_AUDIT_FILE = ROOT / "data" / "raw" / "additional_house_listing_urls.txt"

BASE_URL = "https://www.property.co.zw"
LISTINGS_URL = f"{BASE_URL}/houses-for-sale"

TARGET_LISTINGS = 2400
PAGE_SIZE = 20
MAX_PAGES_PER_RANGE = 100

SEARCH_DELAY = 1.5
LISTING_DELAY = 2.0

PRICE_RANGES = [
    (0, 100000),
    (100001, 200000),
    (200001, 300000),
    (300001, 500000),
    (500001, 1000000),
    (1000001, 10000000),
]


def load_existing():
    """Load existing CSV and verify its schema."""

    if not OUTPUT_FILE.exists():
        raise FileNotFoundError(
            f"Existing dataset not found: {OUTPUT_FILE}"
        )

    with OUTPUT_FILE.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)
        headers = reader.fieldnames or []

        if headers != scraper.COLUMNS:
            raise ValueError(
                "CSV schema mismatch. No data was changed.\n"
                f"Expected: {scraper.COLUMNS}\n"
                f"Found: {headers}"
            )

        rows = list(reader)

    existing_ids = {
        row["listing_id"].strip().upper()
        for row in rows
        if row.get("listing_id", "").strip()
    }

    if len(existing_ids) != len(rows):
        print(
            "WARNING: Existing CSV contains duplicate or blank IDs."
        )

    return rows, existing_ids


def make_listing_params(low, high, page):
    """Build parameters for the direct listings route."""

    params = {
        "maxprice": str(high),
    }

    if low > 0:
        params["minprice"] = str(low)

    if page > 1:
        params["page"] = str(page)

    return params


def extract_total(soup):
    """Read total listing count from the page title."""

    title = (
        soup.title.get_text(" ", strip=True)
        if soup.title else ""
    )

    match = re.search(
        r"([\d,]+)\s+listings",
        title,
        re.IGNORECASE
    )

    if not match:
        return None

    return int(match.group(1).replace(",", ""))


def id_from_url(url):
    """Extract canonical listing ID from a listing URL."""

    match = re.search(
        r"/(?:houses|townhouses)-([^/?#]+)",
        url,
        re.IGNORECASE
    )

    return match.group(1).upper() if match else ""


def extract_house_urls(soup):
    """Extract house and townhouse URLs from result cards."""

    found = set()
    anchors = soup.select(".ResultCardItem a[href]")

    if not anchors:
        anchors = soup.find_all("a", href=True)

    for anchor in anchors:
        href = anchor.get("href", "").strip()
        full_url = urldefrag(urljoin(BASE_URL, href))[0]
        path = urlparse(full_url).path

        if (
            urlparse(full_url).netloc.lower() == urlparse(BASE_URL).netloc.lower()
            and re.match(
                r"^/for-sale/(?:houses|townhouses)-[^/?#]+$",
                path,
                re.IGNORECASE
            )
        ):
            found.add(full_url)

    return found


def get_query_value(url, key):
    values = parse_qs(
        urlparse(url).query
    ).get(key)

    return values[0] if values else None


def fetch_listing_page(http, low, high, page):
    """
    Fetch a direct listings page.

    Refuses to accept a response if the website silently removes
    the requested page number or price filters.
    """

    response = http.get(
        LISTINGS_URL,
        params=make_listing_params(low, high, page),
        timeout=40,
    )

    response.raise_for_status()

    final_url = response.url

    actual_page = get_query_value(final_url, "page")

    if page == 1:
        if actual_page not in (None, "1"):
            raise RuntimeError(
                f"Requested page 1 but received page {actual_page}."
            )
    elif actual_page != str(page):
        raise RuntimeError(
            f"Requested page {page}, but the website returned "
            f"page {actual_page}. Final URL: {final_url}"
        )

    actual_max = get_query_value(final_url, "maxprice")
    actual_min = get_query_value(final_url, "minprice")

    if actual_max != str(high):
        raise RuntimeError(
            f"Maximum price filter was lost. "
            f"Expected {high}; received {actual_max}."
        )

    expected_min = str(low) if low > 0 else None

    if actual_min != expected_min:
        raise RuntimeError(
            f"Minimum price filter was lost. "
            f"Expected {expected_min}; received {actual_min}."
        )

    soup = BeautifulSoup(response.text, "lxml")

    return soup


def collect_urls():
    """
    Discover listings across all six price ranges.

    Uses listing IDs as dictionary keys so the same listing
    cannot be counted twice across different price ranges.
    """

    all_urls = {}
    range_errors = []

    http = scraper.session

    print("\nSTAGE 1 - DISCOVERING HOUSE LISTINGS")
    print("Direct route:", LISTINGS_URL)

    for low, high in PRICE_RANGES:

        print(f"\nPrice range: ${low:,} - ${high:,}")

        range_urls = {}

        try:
            first_soup = fetch_listing_page(
                http, low, high, 1
            )

            total = extract_total(first_soup)

            if total is None:
                raise RuntimeError(
                    "Could not read listing count from page title."
                )

            estimated_pages = max(
                1,
                math.ceil(total / PAGE_SIZE)
            )

            page_limit = min(
                estimated_pages,
                MAX_PAGES_PER_RANGE
            )

            print("Website listing count:", total)
            print("Estimated pages:", estimated_pages)

            for page in range(1, page_limit + 1):

                if page == 1:
                    page_soup = first_soup
                else:
                    time.sleep(SEARCH_DELAY)

                    page_soup = fetch_listing_page(
                        http, low, high, page
                    )

                page_urls = extract_house_urls(page_soup)

                if not page_urls:
                    print(
                        f"Page {page}: no listing URLs. "
                        "Stopping this range."
                    )
                    break

                new_on_page = 0

                for url in page_urls:
                    listing_id = id_from_url(url)

                    if not listing_id:
                        continue

                    if listing_id not in range_urls:
                        range_urls[listing_id] = url
                        new_on_page += 1

                print(
                    f"Page {page}: {len(page_urls)} URLs; "
                    f"{new_on_page} new unique IDs"
                )

            print(
                "Unique listings in this price range:",
                len(range_urls)
            )

            # Merge by canonical ID, deduplicating across ranges.
            before = len(all_urls)

            for listing_id, url in range_urls.items():
                all_urls.setdefault(listing_id, url)

            print(
                "New unique IDs added across all ranges:",
                len(all_urls) - before
            )

        except (requests.RequestException, RuntimeError) as exc:

            message = (
                f"${low:,}-${high:,}: {exc}"
            )

            range_errors.append(message)

            print("PRICE RANGE ERROR:", message)

    print("\nDISCOVERY COMPLETE")
    print("Unique listing IDs discovered:", len(all_urls))

    return list(all_urls.values()), range_errors


def is_valid_asking_price(value):
    """Accept one positive numeric asking price, not ranges or text quotes."""
    if value is None:
        return False

    cleaned = str(value).strip().replace(",", "")
    cleaned = re.sub(r"^(?:USD|US\$|\$)\s*", "", cleaned, flags=re.IGNORECASE)

    # A single numeric value only; reject ranges, negotiable text and blanks.
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", cleaned):
        return False

    try:
        return math.isfinite(float(cleaned)) and float(cleaned) > 0
    except ValueError:
        return False


def append_new_records(urls, existing_ids):
    """Parse and append new records until the target is reached."""

    new_count = 0
    failed_count = 0
    skipped_count = 0

    pending = []

    for url in urls:
        listing_id = id_from_url(url)

        if listing_id and listing_id not in existing_ids:
            pending.append(url)

    # Deterministic random ordering across price ranges.
    random.Random(42).shuffle(pending)

    print("\nSTAGE 2 - EXTRACTING LISTING DETAILS")
    print("Existing unique records:", len(existing_ids))
    print("New candidate URLs:", len(pending))
    print("Target:", TARGET_LISTINGS)

    if len(existing_ids) >= TARGET_LISTINGS:
        print("Target already reached.")
        return new_count, failed_count, skipped_count, existing_ids

    with OUTPUT_FILE.open(
        "a", newline="", encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=scraper.COLUMNS
        )

        for index, url in enumerate(pending, start=1):

            if len(existing_ids) >= TARGET_LISTINGS:
                print("\nTarget reached. Stopping extraction.")
                break

            expected_id = id_from_url(url)

            if not expected_id or expected_id in existing_ids:
                skipped_count += 1
                continue

            print(f"\n[{index}/{len(pending)}] {url}")

            time.sleep(LISTING_DELAY)

            try:
                record = scraper.parse_listing(url)

                if not record:
                    failed_count += 1
                    print("No listing data returned. Skipped.")
                    continue

                record_id = (
                    record.get("listing_id") or ""
                ).strip().upper()

                if not record_id:
                    failed_count += 1
                    print("Missing listing ID. Skipped.")
                    continue

                if record_id != expected_id:
                    failed_count += 1
                    print(
                        "Listing ID mismatch. "
                        f"URL: {expected_id}; parser: {record_id}"
                    )
                    continue

                if record_id in existing_ids:
                    skipped_count += 1
                    print("Duplicate listing. Skipped.")
                    continue

                if (
                    not is_valid_asking_price(record.get("price"))
                    or not record.get("currency")
                ):
                    failed_count += 1
                    print("Missing, non-numeric or invalid price/currency. Skipped.")
                    continue

                writer.writerow({
                    column: record.get(column, "")
                    for column in scraper.COLUMNS
                })

                file.flush()

                existing_ids.add(record_id)
                new_count += 1

                print(
                    f"SAVED {record_id} | "
                    f"{record.get('currency')} "
                    f"{record.get('price')} | "
                    f"{record.get('city')}"
                )

                print(
                    "Total unique records:",
                    len(existing_ids)
                )

            except requests.RequestException as exc:
                failed_count += 1
                print("Request failed:", exc)

            except Exception as exc:
                failed_count += 1
                print("Extraction error:", repr(exc))

    return new_count, failed_count, skipped_count, existing_ids


def main():

    print("=" * 68)
    print("ZIMBABWE HOUSE PRICE PROJECT - ADDITIONAL COLLECTION")
    print("=" * 68)

    rows, existing_ids = load_existing()

    print("Current CSV rows:", len(rows))
    print("Current unique listing IDs:", len(existing_ids))

    if len(existing_ids) >= TARGET_LISTINGS:
        print("Target already reached. No changes made.")
        return

    urls, range_errors = collect_urls()

    URL_AUDIT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    URL_AUDIT_FILE.write_text(
        "\n".join(urls) + ("\n" if urls else ""),
        encoding="utf-8"
    )

    print("\nURL audit saved:", URL_AUDIT_FILE)

    # Do not append a potentially incomplete collection if a range failed.
    if range_errors:
        print("\nCOLLECTION PAUSED.")
        print(
            "At least one price range had an error. "
            "No records were appended."
        )

        for error in range_errors:
            print(" -", error)

        return

    new_candidates = [
        url for url in urls
        if id_from_url(url) not in existing_ids
    ]

    print(
        "\nNew candidate URLs after deduplication:",
        len(new_candidates)
    )

    if not new_candidates:
        print("No additional listings found.")
        return

    # Back up the existing CSV immediately before appending.
    backup = OUTPUT_FILE.with_name(
        "house_listings_before_direct_pagination_"
        f"{datetime.now():%Y%m%d_%H%M%S_%f}.csv"
    )

    shutil.copy2(OUTPUT_FILE, backup)

    print("Backup created:", backup)

    new_count, failed_count, skipped_count, final_ids = (
        append_new_records(urls, existing_ids)
    )

    print("\n" + "=" * 68)
    print("COLLECTION SUMMARY")
    print("=" * 68)

    print("New records appended:", new_count)
    print("Failed or incomplete:", failed_count)
    print("Duplicates skipped:", skipped_count)
    print("Final unique listing IDs:", len(final_ids))
    print("Target:", TARGET_LISTINGS)
    print("Target reached:", len(final_ids) >= TARGET_LISTINGS)
    print("Main CSV:", OUTPUT_FILE)
    print("URL audit:", URL_AUDIT_FILE)
    print("Backup:", backup)


if __name__ == "__main__":
    main()
