import json
import joblib
import numpy as np
import pandas as pd

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
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
    """
    Create a numerically more stable Linear Regression pipeline.

    Median imputation handles missing numeric values. RobustScaler
    reduces the influence of differences in numeric feature scales
    and extreme measurements. One-hot encoding handles categories.
    """

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(
            strategy="median",
            add_indicator=True
        )),
        ("scaler", RobustScaler())
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

    return Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", LinearRegression())
    ])


def evaluate_model(y_test, predictions):
    """Calculate standard regression evaluation metrics."""

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)

    return {
        "MAE_USD": float(mae),
        "RMSE_USD": float(rmse),
        "R2": float(r2)
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

    # Check currency consistency
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

    # Keep the same fixed split for fair model comparisons
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    print("\nDATA SPLIT")
    print("Training records:", len(X_train))
    print("Testing records:", len(X_test))

    results = {}
    prediction_data = pd.DataFrame({
        "actual_price_USD": y_test.values
    }, index=y_test.index)

    models = {}

    # Model 1: Linear Regression on original asking prices
    raw_model = create_pipeline()
    raw_model.fit(X_train, y_train)

    raw_predictions = raw_model.predict(X_test)

    if not np.isfinite(raw_predictions).all():
        raise ValueError(
            "Raw Linear Regression produced non-finite predictions."
        )

    # Asking prices cannot be negative
    raw_predictions = np.maximum(raw_predictions, 0)

    results["linear_raw"] = evaluate_model(
        y_test, raw_predictions
    )

    prediction_data["linear_raw_prediction"] = raw_predictions
    models["linear_raw"] = raw_model

    # Model 2: Linear Regression on log-transformed asking prices
    log_model = create_pipeline()

    log_y_train = np.log1p(y_train)

    log_model.fit(X_train, log_y_train)

    log_predictions_transformed = log_model.predict(X_test)

    if not np.isfinite(log_predictions_transformed).all():
        raise ValueError(
            "Log Linear Regression produced non-finite predictions."
        )

    # Prevent extreme extrapolations when converting back to USD.
    # The upper limit is the largest asking price in the training set,
    # not the test set. This avoids using test-target information.
    max_training_log_price = np.log1p(y_train.max())

    log_predictions_transformed = np.clip(
        log_predictions_transformed,
        0,
        max_training_log_price
    )

    log_predictions = np.expm1(
        log_predictions_transformed
    )

    results["linear_log"] = evaluate_model(
        y_test, log_predictions
    )

    prediction_data["linear_log_prediction"] = log_predictions
    models["linear_log"] = log_model

    # Display results
    print("\nMODEL COMPARISON")

    for model_name, metrics in results.items():
        print(f"\n{model_name.upper()}")
        print("MAE (USD):", round(metrics["MAE_USD"], 2))
        print("RMSE (USD):", round(metrics["RMSE_USD"], 2))
        print("R-squared:", round(metrics["R2"], 4))

    # Save both trained models
    for model_name, model in models.items():
        model_path = MODEL_DIR / f"{model_name}.joblib"
        joblib.dump(model, model_path)
        print("\nSaved model:", model_path)

    # Save evaluation metrics
    metrics_path = RESULTS_DIR / "baseline_model_results.json"

    with open(metrics_path, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)

    # Save test-set predictions for residual analysis
    predictions_path = RESULTS_DIR / "baseline_predictions.csv"

    prediction_data.to_csv(
        predictions_path,
        index_label="row_index"
    )

    print("\nSaved metrics:", metrics_path)
    print("Saved predictions:", predictions_path)
    print("\nBASELINE TRAINING COMPLETED")


if __name__ == "__main__":
    train_model()
