
import re
import shutil
from pathlib import Path
from datetime import datetime

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV_FILE = ROOT / "data" / "raw" / "house_listings.csv"

# Preserve the original dataset before making changes.
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_FILE = CSV_FILE.with_name(
    f"house_listings_backup_{timestamp}.csv"
)

shutil.copy2(CSV_FILE, BACKUP_FILE)

df = pd.read_csv(CSV_FILE)

# Keep original IDs for auditing.
if "original_listing_id" not in df.columns:
    df["original_listing_id"] = df["listing_id"]

def extract_id(url):
    match = re.search(
        r"/houses-([^/?#]+)",
        str(url),
        re.IGNORECASE
    )

    return match.group(1).upper() if match else None

df["corrected_id"] = df["listing_url"].apply(extract_id)

if df["corrected_id"].isna().any():
    raise ValueError("Some listing URLs do not contain an extractable ID.")

if df["corrected_id"].duplicated().any():
    raise ValueError("Duplicate IDs found. No changes saved.")

changed = (
    df["listing_id"].astype(str).str.upper()
    != df["corrected_id"]
)

df["listing_id"] = df["corrected_id"]
df.drop(columns=["corrected_id"], inplace=True)

df.to_csv(CSV_FILE, index=False)

print("LISTING ID CORRECTION COMPLETE")
print("Records checked:", len(df))
print("IDs corrected:", int(changed.sum()))
print("Unique IDs:", df["listing_id"].nunique())
print("Duplicate IDs:", df["listing_id"].duplicated().sum())
print("Backup saved:", BACKUP_FILE)
print("Updated dataset:", CSV_FILE)
