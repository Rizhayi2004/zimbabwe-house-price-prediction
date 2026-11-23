
import joblib
import pandas as pd

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.inspection import permutation_importance


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "cleaned_house_listings.csv"
)

MODEL_FILE = PROJECT_ROOT / "models" / "extra_trees.joblib"

OUTPUT_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "extra_trees_feature_importance.csv"
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

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    model = joblib.load(MODEL_FILE)

    print("Calculating Extra Trees permutation importance...")
    print("Test records:", len(X_test))

    importance = permutation_importance(
        model,
        X_test,
        y_test,
        scoring="neg_mean_absolute_error",
        n_repeats=10,
        random_state=42,
        n_jobs=1
    )

    results = pd.DataFrame({
        "feature": FEATURES,
        "importance_mean": importance.importances_mean,
        "importance_std": importance.importances_std
    })

    results = results.sort_values(
        "importance_mean",
        ascending=False
    )

    results.to_csv(OUTPUT_FILE, index=False)

    print("\nEXTRA TREES FEATURE IMPORTANCE")
    print(results.to_string(index=False))

    print("\nSaved:", OUTPUT_FILE)
    print("\nEXTRA TREES FEATURE IMPORTANCE COMPLETED")


if __name__ == "__main__":
    main()
