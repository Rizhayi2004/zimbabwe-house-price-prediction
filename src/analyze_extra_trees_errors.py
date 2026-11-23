
import joblib
import numpy as np
import pandas as pd

from pathlib import Path
from sklearn.model_selection import train_test_split


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "cleaned_house_listings.csv"
)

MODEL_FILE = PROJECT_ROOT / "models" / "extra_trees.joblib"

OUTPUT_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "extra_trees_error_analysis.csv"
)

NUMERIC_FEATURES = [
    "bedrooms",
    "bathrooms",
    "land_size",
    "floor_size",
    "garages"
]

CATEGORICAL_FEATURES = [
    "city",
    "suburb",
    "property_type"
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def main():

    df = pd.read_csv(DATA_FILE)

    df["price"] = pd.to_numeric(
        df["price"], errors="coerce"
    )

    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    df = df.dropna(subset=["price", "currency"])
    df = df[df["price"] > 0].copy()

    currencies = (
        df["currency"].astype(str).str.upper().unique()
    )

    if len(currencies) != 1 or currencies[0] != "USD":
        raise ValueError(
            f"Expected USD-only data. Found: {currencies}"
        )

    X = df[FEATURES]
    y = df["price"]

    _, X_test, _, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    model = joblib.load(MODEL_FILE)

    predictions = model.predict(X_test)
    predictions = np.maximum(predictions, 0)

    report = df.loc[X_test.index].copy()

    report["actual_price_USD"] = y_test
    report["extra_trees_prediction"] = predictions

    report["absolute_error"] = abs(
        report["actual_price_USD"]
        - report["extra_trees_prediction"]
    )

    report["percentage_error"] = (
        report["absolute_error"]
        / report["actual_price_USD"]
    ) * 100

    report = report.sort_values(
        "absolute_error",
        ascending=False
    )

    report.to_csv(OUTPUT_FILE, index=False)

    columns = [
        "listing_id",
        "actual_price_USD",
        "extra_trees_prediction",
        "absolute_error",
        "percentage_error",
        "bedrooms",
        "bathrooms",
        "land_size",
        "floor_size",
        "city",
        "suburb",
        "property_type"
    ]

    print("\nTOP 20 EXTRA TREES PREDICTION ERRORS")
    print(report[columns].head(20).to_string(index=False))

    print("\nSaved error analysis:", OUTPUT_FILE)
    print("\nEXTRA TREES ERROR ANALYSIS COMPLETED")


if __name__ == "__main__":
    main()
