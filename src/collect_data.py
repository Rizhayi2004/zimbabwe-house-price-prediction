
import pandas as pd
from pathlib import Path
from datetime import date

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Dataset destination
DATA_DIR = PROJECT_ROOT / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = DATA_DIR / "house_listings.csv"

# Fields to collect for each house listing
COLUMNS = [
    "listing_id",
    "title",
    "price",
    "currency",
    "city",
    "suburb",
    "bedrooms",
    "bathrooms",
    "land_size",
    "floor_size",
    "garages",
    "property_type",
    "description",
    "listing_url",
    "image_filename",
    "date_collected"
]

def create_dataset_template():
    """Create an empty dataset with the required columns."""
    if OUTPUT_FILE.exists():
        print(f"Dataset already exists: {OUTPUT_FILE}")
        return

    df = pd.DataFrame(columns=COLUMNS)
    df.to_csv(OUTPUT_FILE, index=False)

    print("Dataset template created successfully.")
    print(f"File location: {OUTPUT_FILE}")
    print(f"Number of columns: {len(COLUMNS)}")
    print(f"Collection date: {date.today()}")

if __name__ == "__main__":
    create_dataset_template()
