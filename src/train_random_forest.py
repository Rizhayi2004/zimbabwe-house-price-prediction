
import json
import joblib
import numpy as np
import pandas as pd

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# Project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "cleaned_house_listings.csv"
)

MODEL_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "data" / "processed"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# Features
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


def create_pipeline():
    """Create a Random Forest regression pipeline."""

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(
            strategy="median",
            add_indicator=True
        ))
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(
            strategy="constant",
            fill_value="Missing"
        )),
        ("encoder", OneHotEncoder(
            handle_unknown="ignore"
        ))
    ])

    preprocessor = ColumnTransformer([
        ("numeric", numeric_pipeline, NUMERIC_FEATURES),
        ("categorical", categorical_pipeline, CATEGORICAL_FEATURES)
    ])

    model = RandomForestRegressor(
        n_estimators=500,
        min_samples_leaf=2,
        max_features=0.8,
        random_state=42,
        n_jobs=-1
    )

    return Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", model)
    ])


def evaluate_model(y_test, predictions):
    """Calculate regression evaluation metrics."""

    return {
        "MAE_USD": float(
            mean_absolute_error(y_test, predictions)
        ),
        "RMSE_USD": float(
            np.sqrt(mean_squared_error(y_test, predictions))
        ),
        "R2": float(
            r2_score(y_test, predictions)
        )
    }


def train_model():

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    if df.empty:
        raise ValueError("Dataset is empty.")

    required = FEATURES + ["price", "currency"]

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Convert numeric columns safely
    df["price"] = pd.to_numeric(
        df["price"], errors="coerce"
    )

    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    # Retain valid asking prices
    df = df.dropna(subset=["price", "currency"])
    df = df[df["price"] > 0].copy()

    # Confirm currency consistency
    currencies = (
        df["currency"].astype(str).str.upper().unique()
    )

    if len(currencies) != 1 or currencies[0] != "USD":
        raise ValueError(
            f"Expected USD-only data. Found: {currencies}"
        )

    print("\nDATASET")
    print("Records:", len(df))
    print("Currency:", currencies[0])

    X = df[FEATURES]
    y = df["price"]

    # Same split as the Linear Regression baseline
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    print("\nDATA SPLIT")
    print("Training records:", len(X_train))
    print("Testing records:", len(X_test))

    # Train Random Forest
    model = create_pipeline()

    print("\nTraining Random Forest...")
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    if not np.isfinite(predictions).all():
        raise ValueError(
            "Random Forest produced non-finite predictions."
        )

    # Asking prices cannot be negative
    predictions = np.maximum(predictions, 0)

    # Evaluate
    results = {
        "random_forest": evaluate_model(
            y_test, predictions
        )
    }

    metrics = results["random_forest"]

    print("\nRANDOM FOREST RESULTS")
    print("MAE (USD):", round(metrics["MAE_USD"], 2))
    print("RMSE (USD):", round(metrics["RMSE_USD"], 2))
    print("R-squared:", round(metrics["R2"], 4))

    # Save trained model
    model_path = MODEL_DIR / "random_forest.joblib"
    joblib.dump(model, model_path)

    print("\nSaved model:", model_path)

    # Save evaluation metrics
    metrics_path = (
        RESULTS_DIR / "random_forest_model_results.json"
    )

    with open(metrics_path, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)

    # Save predictions for residual analysis
    prediction_data = pd.DataFrame({
        "actual_price_USD": y_test.values,
        "random_forest_prediction": predictions
    }, index=y_test.index)

    predictions_path = (
        RESULTS_DIR / "random_forest_predictions.csv"
    )

    prediction_data.to_csv(
        predictions_path,
        index_label="row_index"
    )

    print("Saved metrics:", metrics_path)
    print("Saved predictions:", predictions_path)

    print("\nRANDOM FOREST TRAINING COMPLETED")


if __name__ == "__main__":
    train_model()
