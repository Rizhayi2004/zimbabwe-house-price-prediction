
import json
import time
from pathlib import Path
from urllib.parse import urlparse
from io import BytesIO

import pandas as pd
import requests
from PIL import Image


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CSV_FILE = PROJECT_ROOT / "data" / "raw" / "house_listings.csv"
IMAGE_DIR = PROJECT_ROOT / "images" / "original"

MANIFEST_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "image_download_manifest.csv"
)


# ============================================================
# DOWNLOAD SETTINGS
# ============================================================

REQUEST_DELAY = 1.0
TIMEOUT = 40

MAX_IMAGES_PER_LISTING = 1

# Temporary test limit: only 3 listings without images.
# Change to None after the test succeeds to process all listings.
TEST_LIMIT = None

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; "
        "ZimbabweHousePriceResearch/1.0)"
    )
}

session = requests.Session()
session.headers.update(HEADERS)


# ============================================================
# IMAGE UTILITIES
# ============================================================

def get_extension(content_type):

    content_type = content_type.lower()

    if "webp" in content_type:
        return ".webp"

    if "png" in content_type:
        return ".png"

    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"

    return None


def has_existing_image(listing_id):

    return any(
        IMAGE_DIR.glob(f"{listing_id}_*")
    )


def download_image(listing_id, image_url):

    try:

        response = session.get(
            image_url,
            timeout=TIMEOUT
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type", ""
        ).split(";")[0].lower()

        if not content_type.startswith("image/"):

            print(
                f"Skipped {listing_id}: "
                "response is not an image"
            )

            return None

        extension = get_extension(content_type)

        if extension is None:

            print(
                f"Skipped {listing_id}: "
                "unsupported image format"
            )

            return None

        image_bytes = response.content

        # Verify image integrity before saving.
        with Image.open(BytesIO(image_bytes)) as image:
            image.verify()

        filename = f"{listing_id}_1{extension}"

        image_path = IMAGE_DIR / filename

        # Never overwrite an existing image.
        if image_path.exists():
            return filename

        with open(image_path, "wb") as image_file:
            image_file.write(image_bytes)

        print(f"Downloaded: {filename}")

        return filename

    except Exception as error:

        print(
            f"Failed {listing_id}: {error}"
        )

        return None


# ============================================================
# MAIN DOWNLOADER
# ============================================================

def main():

    IMAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    MANIFEST_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df = pd.read_csv(CSV_FILE)

    results = []

    total = len(df)

    downloaded = 0
    skipped = 0
    failed = 0

    tested = 0

    print("=" * 65)
    print("ZIMBABWE HOUSE PRICE PROJECT - IMAGE DOWNLOADER")
    print("=" * 65)

    print("Total listings:", total)
    print("Image folder:", IMAGE_DIR)
    print("Images per listing:", MAX_IMAGES_PER_LISTING)
    print("Test limit:", TEST_LIMIT)

    print()

    for index, row in df.iterrows():

        listing_id = str(row["listing_id"])

        # Preserve existing downloaded images.
        if has_existing_image(listing_id):

            skipped += 1

            results.append({
                "listing_id": listing_id,
                "image_file": "",
                "status": "already_exists"
            })

            continue

        # Count only listings that need downloading.
        tested += 1

        # Stop after the temporary test limit.
        if TEST_LIMIT is not None and tested > TEST_LIMIT:
            break

        raw_urls = row.get("image_urls", "[]")

        try:

            urls = (
                json.loads(raw_urls)
                if pd.notna(raw_urls)
                else []
            )

        except (json.JSONDecodeError, TypeError):

            urls = []

        if not isinstance(urls, list) or not urls:

            failed += 1

            results.append({
                "listing_id": listing_id,
                "image_file": "",
                "status": "no_image_url"
            })

            pd.DataFrame(results).to_csv(
                MANIFEST_FILE,
                index=False
            )

            continue

        filename = None

        # Try available image URLs until one works.
        for image_url in urls:

            if not isinstance(image_url, str):
                continue

            if urlparse(image_url).scheme not in (
                "http",
                "https"
            ):
                continue

            filename = download_image(
                listing_id,
                image_url
            )

            if filename:
                break

            time.sleep(REQUEST_DELAY)

        if filename:

            downloaded += 1
            status = "downloaded"

        else:

            failed += 1
            status = "failed"

        results.append({
            "listing_id": listing_id,
            "image_file": filename or "",
            "status": status
        })

        # Save progress after every processed listing.
        pd.DataFrame(results).to_csv(
            MANIFEST_FILE,
            index=False
        )

        if tested % 25 == 0:

            print(
                f"Progress: {tested} | "
                f"Downloaded: {downloaded} | "
                f"Skipped: {skipped} | "
                f"Failed: {failed}"
            )

        time.sleep(REQUEST_DELAY)

    # Final manifest save.
    pd.DataFrame(results).to_csv(
        MANIFEST_FILE,
        index=False
    )

    print()
    print("=" * 65)
    print("IMAGE DOWNLOAD SUMMARY")
    print("=" * 65)

    print("Total listings:", total)
    print("New images downloaded:", downloaded)
    print("Existing images skipped:", skipped)
    print("Failed or unavailable:", failed)

    print("Manifest:", MANIFEST_FILE)


if __name__ == "__main__":

    main()
