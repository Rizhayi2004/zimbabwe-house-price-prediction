
import csv
import json
import re
import time
import mimetypes
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# =========================================================
# PROJECT SETTINGS
# =========================================================

ROOT = Path(__file__).resolve().parent.parent

OUTPUT_FILE = ROOT / "data" / "raw" / "house_listings.csv"
IMAGE_DIR = ROOT / "images" / "original"

BASE_URL = "https://www.property.co.zw"

TARGET_LISTINGS = 2400
MAX_PAGES = 250

MAX_IMAGES_PER_LISTING = 5
DOWNLOAD_IMAGES = False

REQUEST_DELAY = 2
IMAGE_DELAY = 0.5

HEADERS = {
    "User-Agent": (
        "Academic Research Project - "
        "Zimbabwe House Price Prediction"
    )
}


# =========================================================
# DATASET COLUMNS
# =========================================================

COLUMNS = [
    "listing_id",
    "title",
    "price",
    "currency",
    "city",
    "suburb",
    "region",
    "bedrooms",
    "bathrooms",
    "garages",
    "land_size",
    "floor_size",
    "property_type",
    "description",
    "features",
    "listing_url",
    "image_urls",
    "downloaded_images",
    "date_posted",
    "date_collected",
    "original_listing_id"
]


# =========================================================
# HTTP SESSION AND RETRIES
# =========================================================

session = requests.Session()
session.headers.update(HEADERS)

retry_strategy = Retry(
    total=4,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)

session.mount("https://", adapter)
session.mount("http://", adapter)


# =========================================================
# GENERAL HELPERS
# =========================================================

def clean_text(value):
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def get_first_value(value):
    if isinstance(value, list):
        return value[0] if value else {}

    return value if isinstance(value, dict) else {}


def find_listing_data(data):
    if isinstance(data, dict):

        if data.get("@type") == "RealEstateListing":
            return data

        for value in data.values():
            result = find_listing_data(value)

            if result:
                return result

    elif isinstance(data, list):

        for item in data:
            result = find_listing_data(item)

            if result:
                return result

    return None


# =========================================================
# FIND LISTINGS ACROSS WEBSITE PAGES
# =========================================================

def get_listing_urls(page_number):

    url = f"{BASE_URL}/houses-for-sale?page={page_number}"

    response = session.get(url, timeout=40)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    links = set()

    for link in soup.find_all("a", href=True):

        href = link["href"]

        full_url = urldefrag(urljoin(BASE_URL, href))[0]
        parsed_url = urlparse(full_url)

        if (
            parsed_url.netloc.lower() == urlparse(BASE_URL).netloc.lower()
            and re.match(
                r"^/for-sale/(?:houses|townhouses)-[^/?#]+$",
                parsed_url.path,
                re.IGNORECASE
            )
        ):
            links.add(full_url)

    return sorted(links)


def collect_all_listing_urls():

    all_urls = []
    seen_urls = set()
    empty_pages = 0

    print("\nSCANNING WEBSITE LISTING PAGES")

    for page in range(1, MAX_PAGES + 1):

        print(f"Checking page {page}...")

        try:
            urls = get_listing_urls(page)

        except requests.RequestException as error:

            print("Page request failed:", error)
            break

        new_urls = [
            url for url in urls
            if url not in seen_urls
        ]

        if not new_urls:

            empty_pages += 1

            if empty_pages >= 3:
                break

        else:

            empty_pages = 0

            all_urls.extend(new_urls)
            seen_urls.update(new_urls)

        print(
            f"New links: {len(new_urls)} | "
            f"Total unique links: {len(all_urls)}"
        )

        time.sleep(REQUEST_DELAY)

    print("\nTOTAL UNIQUE RESIDENTIAL LISTING LINKS:", len(all_urls))

    return all_urls


# =========================================================
# EXTRACT BREADCRUMBS
# =========================================================

def extract_breadcrumbs(soup):

    for script in soup.find_all(
        "script",
        type="application/ld+json"
    ):

        try:
            data = json.loads(
                script.string or script.get_text()
            )

        except (json.JSONDecodeError, TypeError):
            continue

        if (
            isinstance(data, dict)
            and data.get("@type") == "BreadcrumbList"
        ):

            items = data.get("itemListElement", [])

            return [
                clean_text(item.get("name"))
                for item in items
                if isinstance(item, dict)
            ]

    return []


def infer_property_type(url, listing, about, breadcrumbs, title, description):
    """Infer the residential property type from structured data and page text.

    URL category is only a fallback: Property.co.zw's townhouses route can
    include flats, apartments and cluster homes as well as townhouses.
    """
    structured_values = []
    for source in (about, listing):
        if isinstance(source, dict):
            for key in ("propertyType", "property_type", "additionalType", "category", "@type"):
                value = source.get(key)
                if isinstance(value, (str, int, float)):
                    structured_values.append(str(value))
                elif isinstance(value, dict):
                    structured_values.extend(
                        str(value.get(k, "")) for k in ("name", "@type")
                    )
                elif isinstance(value, list):
                    structured_values.extend(str(item) for item in value)

    text = " ".join(
        str(value) for value in [*structured_values, *(breadcrumbs or []), title, description]
        if value
    ).lower()

    # More specific subtypes must be checked before the general house terms.
    if re.search(r"\b(apartment|apartments|flat|flats|garden flat)\b", text):
        return "Flat/Apartment"
    if re.search(r"\b(cluster home|cluster homes|cluster house|cluster houses)\b", text):
        return "Cluster Home"
    if re.search(r"\b(semi[- ]detached|townhouse|town house|duplex)\b", text):
        return "Townhouse"
    if re.search(r"\b(detached house|family house|house for sale|house)\b", text):
        return "House"

    path = urlparse(url).path.lower()
    if re.search(r"/for-sale/townhouses-[^/]+$", path):
        return "Townhouse (site category; subtype unclear)"
    if re.search(r"/for-sale/houses-[^/]+$", path):
        return "House"
    return "Other residential"


# =========================================================
# EXTRACT DESCRIPTION AND FEATURES
# =========================================================

def extract_description(soup, listing):

    page_text = soup.get_text(" ", strip=True)

    description = ""

    start = page_text.find("Description")

    if start != -1:

        start += len("Description")

        end = page_text.find("Amenities", start)

        if end != -1:
            description = page_text[start:end].strip()

    if not description:
        description = clean_text(listing.get("description", ""))

    return clean_text(description)


def extract_features(soup):

    page_text = soup.get_text(" ", strip=True)

    features = ""

    start = page_text.find("Amenities")

    if start != -1:

        start += len("Amenities")

        end = page_text.find(
            "Explore home offers",
            start
        )

        if end != -1:
            features = page_text[start:end].strip()

    return clean_text(features)


# =========================================================
# EXTRACT LAND SIZE
# =========================================================

def extract_land_size(description):

    patterns = [
        r"([\d,]+(?:\.\d+)?)\s*(?:m²|sqm|sq\.?\s*m)",
        r"([\d,]+(?:\.\d+)?)\s*(?:square metres|square meters)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            description,
            re.IGNORECASE
        )

        if match:

            return float(
                match.group(1).replace(",", "")
            )

    return ""


# =========================================================
# EXTRACT GARAGE COUNT
# =========================================================

def extract_garages(description):

    counts = []

    numeric_patterns = [
        r"\b(\d+)\s*[- ]?(?:car\s+)?(?:lock[- ]?up\s+)?garages?\b",
        r"\b(\d+)\s*[- ]?car\s+garage\b"
    ]

    word_counts = {
        "single": 1,
        "double": 2,
        "triple": 3
    }

    for pattern in numeric_patterns:

        matches = re.findall(
            pattern,
            description,
            re.IGNORECASE
        )

        counts.extend(int(value) for value in matches)

    for word, number in word_counts.items():

        if re.search(
            rf"\b{word}\s+(?:lock[- ]?up\s+)?garage\b",
            description,
            re.IGNORECASE
        ):

            counts.append(number)

    return max(counts) if counts else ""


# =========================================================
# EXTRACT IMAGE URLS
# =========================================================

def extract_image_urls(listing, about, soup):

    images = listing.get("image", [])

    if not images:
        images = about.get("image", [])

    if isinstance(images, str):
        images = [images]

    if isinstance(images, dict):
        images = [images]

    image_urls = []

    for item in images:

        if isinstance(item, dict):
            image_url = item.get("url", "")

        else:
            image_url = item

        if not image_url:
            continue

        image_url = urljoin(BASE_URL, image_url)

        if image_url not in image_urls:
            image_urls.append(image_url)

    # Include Open Graph image if structured data has none.
    if not image_urls:

        og_image = soup.find(
            "meta",
            property="og:image"
        )

        if og_image and og_image.get("content"):

            image_urls.append(
                urljoin(BASE_URL, og_image["content"])
            )

    return image_urls


# =========================================================
# DOWNLOAD PROPERTY PHOTOGRAPHS
# =========================================================

def download_listing_images(listing_id, image_urls):

    IMAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    downloaded_files = []

    if not DOWNLOAD_IMAGES:
        return downloaded_files

    selected_images = image_urls[:MAX_IMAGES_PER_LISTING]

    for index, image_url in enumerate(
        selected_images,
        start=1
    ):

        try:

            response = session.get(
                image_url,
                timeout=40
            )

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type",
                ""
            ).split(";")[0].lower()

            if not content_type.startswith("image/"):
                continue

            extension = mimetypes.guess_extension(
                content_type
            ) or ".jpg"

            if extension == ".jpe":
                extension = ".jpg"

            filename = (
                f"{listing_id}_{index}{extension}"
            )

            image_path = IMAGE_DIR / filename

            with open(image_path, "wb") as image_file:
                image_file.write(response.content)

            downloaded_files.append(filename)

            print("Downloaded image:", filename)

            time.sleep(IMAGE_DELAY)

        except requests.RequestException as error:

            print(
                f"Image download failed for {listing_id}:",
                error
            )

    return downloaded_files


def is_valid_asking_price(value):
    """Accept one positive numeric asking price, not ranges or text quotes."""
    if value is None:
        return False
    cleaned = str(value).strip().replace(",", "")
    cleaned = re.sub(r"^(?:USD|US\$|\$)\s*", "", cleaned, flags=re.IGNORECASE)
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", cleaned):
        return False
    try:
        return float(cleaned) > 0
    except ValueError:
        return False


# =========================================================
# PARSE INDIVIDUAL PROPERTY LISTING
# =========================================================

def parse_listing(url):

    response = session.get(
        url,
        timeout=40
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "lxml"
    )

    listing = None

    for script in soup.find_all(
        "script",
        type="application/ld+json"
    ):

        try:

            data = json.loads(
                script.string or script.get_text()
            )

        except (json.JSONDecodeError, TypeError):
            continue

        result = find_listing_data(data)

        if result:
            listing = result
            break

    if not listing:

        print("No structured listing data:", url)
        return None

    about = get_first_value(
        listing.get("about")
    )

    offer = get_first_value(
        listing.get("offers")
    )

    address = get_first_value(
        about.get("address")
    )

    floor = get_first_value(
        about.get("floorSize")
    )

    breadcrumbs = extract_breadcrumbs(soup)

    city = (
        breadcrumbs[1]
        if len(breadcrumbs) > 1
        else ""
    )

    description = extract_description(
        soup,
        listing
    )

    features = extract_features(soup)

    land_size = extract_land_size(description)

    garages = extract_garages(description)

    image_urls = extract_image_urls(
        listing,
        about,
        soup
    )

    # Preserve the identifier supplied by the website for auditing.
    original_listing_id = clean_text(
        listing.get("identifier", "")
    )

    # Use the ID embedded in the listing URL as the canonical ID.
    # This matches the verified IDs already stored in the CSV.
    id_match = re.search(
        r"/(?:houses|townhouses)-([^/?#]+)",
        url,
        re.IGNORECASE
    )

    listing_id = (
        id_match.group(1).upper()
        if id_match
        else ""
    )

    downloaded_images = download_listing_images(
        listing_id,
        image_urls
    )

    floor_size = (
        floor.get("value", "")
        if isinstance(floor, dict)
        else ""
    )

    record = {

        "listing_id": listing_id,

        "title": clean_text(
            listing.get("name", "")
        ),

        "price": offer.get("price", ""),

        "currency": clean_text(
            offer.get("priceCurrency", "")
        ),

        "city": city,

        "suburb": clean_text(
            address.get("addressLocality", "")
        ),

        "region": clean_text(
            address.get("addressRegion", "")
        ),

        "bedrooms": about.get(
            "numberOfBedrooms", ""
        ),

        "bathrooms": about.get(
            "numberOfBathroomsTotal", ""
        ),

        "garages": garages,

        "land_size": land_size,

        "floor_size": floor_size,

        "property_type": infer_property_type(
            url=url,
            listing=listing,
            about=about,
            breadcrumbs=breadcrumbs,
            title=clean_text(listing.get("name", "")),
            description=description
        ),

        "description": description,

        "features": features,

        "listing_url": listing.get("url", url),

        "image_urls": json.dumps(image_urls),

        "downloaded_images": json.dumps(
            downloaded_images
        ),

        "date_posted": listing.get(
            "datePosted", ""
        ),

        "date_collected": date.today().isoformat(),

        "original_listing_id": original_listing_id
    }

    return record


# =========================================================
# PREPARE CSV AND RESUME EXISTING COLLECTION
# =========================================================

def prepare_output_file():

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if OUTPUT_FILE.exists() and OUTPUT_FILE.stat().st_size > 0:

        with open(
            OUTPUT_FILE,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            existing_columns = next(
                csv.reader(file),
                []
            )

        if existing_columns != COLUMNS:

            backup_file = OUTPUT_FILE.with_name(
                "house_listings_old_schema.csv"
            )

            OUTPUT_FILE.rename(backup_file)

            print(
                "Previous CSV schema backed up to:",
                backup_file
            )

    if not OUTPUT_FILE.exists() or OUTPUT_FILE.stat().st_size == 0:

        with open(
            OUTPUT_FILE,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=COLUMNS
            )

            writer.writeheader()


def load_existing_ids():

    existing_ids = set()

    if OUTPUT_FILE.exists():

        with open(
            OUTPUT_FILE,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                listing_id = row.get("listing_id")

                if listing_id:
                    existing_ids.add(listing_id)

    return existing_ids


# =========================================================
# MAIN COLLECTION PROCESS
# =========================================================

def main():

    print("=" * 60)
    print("ZIMBABWE HOUSE PRICE DATA COLLECTION")
    print("=" * 60)

    prepare_output_file()

    existing_ids = load_existing_ids()

    print(
        "\nAlready collected:",
        len(existing_ids)
    )

    if len(existing_ids) >= TARGET_LISTINGS:

        print("Target already reached.")
        return

    listing_urls = collect_all_listing_urls()

    if not listing_urls:

        print("No eligible house/townhouse listing URLs found.")
        return

    collected = 0
    failed = 0

    for index, url in enumerate(
        listing_urls,
        start=1
    ):

        if len(existing_ids) >= TARGET_LISTINGS:
            break

        print("\n" + "-" * 60)
        print(
            f"Listing {index} of {len(listing_urls)}"
        )
        print("URL:", url)

        time.sleep(REQUEST_DELAY)

        try:

            record = parse_listing(url)

            if not record:
                failed += 1
                continue

            listing_id = record["listing_id"]

            if not listing_id:

                print("Missing listing ID. Skipping.")
                failed += 1
                continue

            if listing_id in existing_ids:

                print("Already collected. Skipping.")
                continue

            if not is_valid_asking_price(record["price"]) or not record["currency"]:

                print("Missing, non-numeric or invalid price/currency. Skipping.")
                failed += 1
                continue

            with open(
                OUTPUT_FILE,
                "a",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=COLUMNS
                )

                writer.writerow(record)

            existing_ids.add(listing_id)
            collected += 1

            print("\nSAVED SUCCESSFULLY")
            print("ID:", listing_id)
            print("Title:", record["title"])
            print(
                "Price:",
                record["currency"],
                record["price"]
            )
            print("City:", record["city"])
            print("Bedrooms:", record["bedrooms"])
            print("Images:", len(
                json.loads(record["image_urls"])
            ))

            print(
                "TOTAL UNIQUE LISTINGS:",
                len(existing_ids)
            )

        except requests.RequestException as error:

            failed += 1
            print("Listing request failed:", error)

        except Exception as error:

            failed += 1
            print("Unexpected error:", error)

    print("\n" + "=" * 60)
    print("COLLECTION SESSION FINISHED")
    print("=" * 60)

    print("New listings collected:", collected)
    print("Failed listings:", failed)
    print("Total unique listings:", len(existing_ids))
    print("Target:", TARGET_LISTINGS)
    print("CSV:", OUTPUT_FILE)
    print("Images:", IMAGE_DIR)


if __name__ == "__main__":
    main()
