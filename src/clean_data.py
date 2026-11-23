
import pandas as pd
from pathlib import Path

# Project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_FILE = PROJECT_ROOT / "data" / "raw" / "house_listings.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_FILE = PROCESSED_DIR / "cleaned_house_listings.csv"
REPORT_FILE = PROCESSED_DIR / "cleaning_report.txt"

NUMERIC_COLUMNS = [
    "price",
    "bedrooms",
    "bathrooms",
    "garages",
    "land_size",
    "floor_size",
]

TEXT_COLUMNS = [
    "currency",
    "city",
    "suburb",
    "region",
    "property_type",
    "title",
    "description",
    "features",
]

# Verified bathroom extraction errors.
# None means the actual bathroom count cannot be confirmed.
BATHROOM_CORRECTIONS = {
    "SARE256485": None,
    "PGP259154": None,
}

# Verified land-size/floor-size extraction corrections.
# None means that the value is not reliably available and must be missing.
SIZE_CORRECTIONS = {
    "SYR240202": {
        "land_size": 157827.54,   # 39 acres
        "floor_size": None,
    },
    "LAW202502": {
        "land_size": 2400.0,      # 2,400 m² stand
        "floor_size": None,
    },
    "SYR257211": {
        "land_size": 17000.0,     # 17,000 m² property
        "floor_size": None,
    },
    "SYR251888": {
        "land_size": 20000.0,     # 2 hectares
        "floor_size": None,
    },
    "SYR238045": {
        "land_size": 16000.0,     # 4 acres, approximately 16,000 m²
        "floor_size": 600.0,      # House area stated in listing
    },
    "SYR256831": {
        "land_size": 16000.0,     # 1.6 hectares
        "floor_size": None,
    },
    "FAC249532": {
        "land_size": 100000.0,    # 10 hectares
        "floor_size": None,
    },
    "PLZP255404": {
        "land_size": 15413.0,     # 1.5413 hectares
        "floor_size": None,
    },
    "RLG257923": {
        "land_size": None,        # No verified land area
        "floor_size": None,       # Extracted 30,000 is not a house floor area
    },
    "FAC251842": {
        "land_size": None,        # No verified land area
        "floor_size": None,       # Extracted 16,000 is not a house floor area
    },
    "SYR258993": {
        "land_size": None,        # No verified land area
        "floor_size": None,       # Extracted 31,775 is not a house floor area
    },
    "CLRP210156": {
        "land_size": 20234.28,    # 5 acres; 220 m² refers to teak decking
        "floor_size": None,       # No verified house floor area
    },
    "SEF209539": {
        "land_size": 157827.54,   # 39 acres
        "floor_size": None,       # No verified house floor area
    },
    "LAW194018": {
        "land_size": 20234.28,    # 5 acres
        "floor_size": None,       # Extracted 999 is unverified
    },
    "PGP212875": {
        "land_size": 1784.0,      # 1,784 m² stand
        "floor_size": None,       # No verified house floor area
    },
    "RED248389": {
        "land_size": None,        # No verified land area
        "floor_size": None,       # Extracted 0.01 is erroneous
    },
}


def require_listing_ids(df, listing_ids, correction_type):
    """Stop if a manually verified correction refers to a missing listing."""
    available_ids = set(df["listing_id"].dropna().astype(str))
    missing_ids = sorted(set(listing_ids) - available_ids)

    if missing_ids:
        raise ValueError(
            f"{correction_type} correction listing IDs not found: "
            f"{missing_ids}"
        )


def values_match(actual, expected):
    """Compare a saved numeric value with an expected value or missing value."""
    if expected is None:
        return pd.isna(actual)

    return pd.notna(actual) and abs(float(actual) - float(expected)) < 0.01


def clean_data():
    """Clean property listings while preserving the original raw dataset."""

    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Raw dataset not found: {RAW_FILE}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(RAW_FILE)
    original_rows = len(df)

    print("=" * 60)
    print("ZIMBABWE HOUSE PRICE DATA CLEANING")
    print("=" * 60)
    print("Original dataset:", df.shape)

    required_columns = [
        "listing_id",
        "price",
        "currency",
        "city",
        "bedrooms",
        "bathrooms",
        "garages",
        "land_size",
        "floor_size",
        "property_type",
    ]

    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Standardise listing IDs before checking correction targets.
    df["listing_id"] = df["listing_id"].astype("string").str.strip()

    # Ensure all manually corrected records are present in the raw dataset.
    require_listing_ids(
        df,
        BATHROOM_CORRECTIONS.keys(),
        "Bathroom",
    )
    require_listing_ids(
        df,
        SIZE_CORRECTIONS.keys(),
        "Size",
    )

    # Remove duplicate listings, keeping the first occurrence.
    duplicate_count = df.duplicated(
        subset=["listing_id"], keep="first"
    ).sum()

    df = df.drop_duplicates(
        subset=["listing_id"], keep="first"
    ).copy()

    # Standardise text fields.
    for column in TEXT_COLUMNS:
        if column in df.columns:
            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
                .replace("", pd.NA)
            )

    df["currency"] = df["currency"].str.upper()

    # Correct whitespace normalisation (one or more whitespace characters).
    df["property_type"] = df["property_type"].str.replace(
        r"\s+", " ", regex=True
    )

    # Convert numeric fields safely.
    conversion_report = {}

    for column in NUMERIC_COLUMNS:
        before_missing = df[column].isna().sum()

        df[column] = pd.to_numeric(
            df[column]
            .astype("string")
            .str.replace(",", "", regex=False),
            errors="coerce",
        )

        after_missing = df[column].isna().sum()
        conversion_report[column] = int(after_missing - before_missing)

    # Remove invalid asking prices.
    invalid_price_count = int(
        (df["price"].isna() | (df["price"] <= 0)).sum()
    )

    df = df[
        df["price"].notna() & (df["price"] > 0)
    ].copy()

    # Apply verified bathroom corrections.
    bathroom_corrections_applied = []

    for listing_id, corrected_value in BATHROOM_CORRECTIONS.items():
        mask = df["listing_id"] == listing_id
        old_value = df.loc[mask, "bathrooms"].iloc[0]

        df.loc[mask, "bathrooms"] = corrected_value

        bathroom_corrections_applied.append({
            "listing_id": listing_id,
            "old_value": old_value,
            "new_value": corrected_value,
        })

    # Apply verified size corrections.
    size_corrections_applied = []

    for listing_id, corrections in SIZE_CORRECTIONS.items():
        mask = df["listing_id"] == listing_id

        old_land_size = df.loc[mask, "land_size"].iloc[0]
        old_floor_size = df.loc[mask, "floor_size"].iloc[0]

        df.loc[mask, "land_size"] = corrections["land_size"]
        df.loc[mask, "floor_size"] = corrections["floor_size"]

        size_corrections_applied.append({
            "listing_id": listing_id,
            "old_land_size": old_land_size,
            "new_land_size": corrections["land_size"],
            "old_floor_size": old_floor_size,
            "new_floor_size": corrections["floor_size"],
        })

    # Convert negative measurements to missing values.
    measurement_columns = [
        "bedrooms",
        "bathrooms",
        "garages",
        "land_size",
        "floor_size",
    ]

    negative_report = {}

    for column in measurement_columns:
        negative_count = int((df[column] < 0).sum())
        negative_report[column] = negative_count
        df.loc[df[column] < 0, column] = pd.NA

    # Save the cleaned dataset. The raw CSV is never modified.
    df.to_csv(PROCESSED_FILE, index=False)

    # Reload and validate the actual saved output.
    check_df = pd.read_csv(PROCESSED_FILE)

    if check_df["listing_id"].duplicated().any():
        raise ValueError("Duplicate listing IDs remain.")

    if check_df["listing_id"].isna().any():
        raise ValueError("Missing listing IDs remain.")

    if check_df["price"].isna().any() or (check_df["price"] <= 0).any():
        raise ValueError("Invalid prices remain.")

    if len(check_df) != len(df):
        raise ValueError("Saved dataset row count mismatch.")

    # Validate every bathroom correction in the saved CSV.
    for listing_id, expected_value in BATHROOM_CORRECTIONS.items():
        row = check_df.loc[check_df["listing_id"] == listing_id]

        if row.empty or not values_match(
            row["bathrooms"].iloc[0], expected_value
        ):
            raise ValueError(
                f"Bathroom correction failed in saved file: {listing_id}"
            )

    # Validate both land_size and floor_size for every corrected listing.
    for listing_id, corrections in SIZE_CORRECTIONS.items():
        row = check_df.loc[check_df["listing_id"] == listing_id]

        if row.empty:
            raise ValueError(
                f"Size correction listing missing from saved file: {listing_id}"
            )

        for column in ("land_size", "floor_size"):
            actual = row[column].iloc[0]
            expected = corrections[column]

            if not values_match(actual, expected):
                raise ValueError(
                    f"{column} correction failed for {listing_id}: "
                    f"expected {expected}, found {actual}"
                )

    # Generate a detailed cleaning report.
    report = [
        "ZIMBABWE HOUSE PRICE PROJECT - CLEANING REPORT",
        "=" * 55,
        f"Original rows: {original_rows}",
        f"Duplicate records removed: {duplicate_count}",
        f"Invalid-price records removed: {invalid_price_count}",
        f"Final cleaned rows: {len(df)}",
        f"Rows removed: {original_rows - len(df)}",
        "",
        "Numeric conversion-created missing values:",
    ]

    for column, count in conversion_report.items():
        report.append(f"{column}: {count}")

    report.extend([
        "",
        "Verified bathroom extraction corrections:",
    ])

    for correction in bathroom_corrections_applied:
        report.append(
            f"{correction['listing_id']}: "
            f"{correction['old_value']} -> Missing"
        )

    report.extend([
        "",
        "Verified land-size/floor-size extraction corrections:",
    ])

    for correction in size_corrections_applied:
        report.append(
            f"{correction['listing_id']}: "
            f"land_size {correction['old_land_size']} -> "
            f"{correction['new_land_size']}; "
            f"floor_size {correction['old_floor_size']} -> "
            f"{correction['new_floor_size']}"
        )

    report.extend([
        "",
        "Negative measurements converted to missing:",
    ])

    for column, count in negative_report.items():
        report.append(f"{column}: {count}")

    report.extend([
        "",
        "Final missing values:",
    ])

    for column, count in df.isna().sum().items():
        report.append(f"{column}: {count}")

    report.extend([
        "",
        f"Final dataset shape: {df.shape}",
        f"Cleaned dataset: {PROCESSED_FILE}",
    ])

    REPORT_FILE.write_text("\n".join(report), encoding="utf-8")

    print("\nCleaning completed successfully.")
    print("Cleaned dataset shape:", df.shape)
    print("Duplicate records removed:", duplicate_count)
    print("Invalid-price records removed:", invalid_price_count)
    print(
        "Bathroom corrections applied:",
        len(bathroom_corrections_applied),
    )
    print(
        "Size corrections applied:",
        len(size_corrections_applied),
    )
    print("Cleaning report:", REPORT_FILE)
    print("Cleaned file:", PROCESSED_FILE)


if __name__ == "__main__":
    clean_data()
