
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "report" / "figures"

PREDICTIONS_FILE = (
    PROCESSED_DIR / "extra_trees_predictions.csv"
)

ERROR_ANALYSIS_FILE = (
    PROCESSED_DIR / "extra_trees_error_analysis.csv"
)

OUTPUT_ACTUAL_PREDICTED = (
    FIGURES_DIR / "extra_trees_actual_vs_predicted.png"
)

OUTPUT_RESIDUALS = (
    FIGURES_DIR / "extra_trees_residuals_vs_predicted.png"
)

OUTPUT_RESIDUAL_DISTRIBUTION = (
    FIGURES_DIR / "extra_trees_residual_distribution.png"
)

OUTPUT_ABSOLUTE_ERRORS = (
    FIGURES_DIR / "extra_trees_absolute_error_distribution.png"
)


def main():

    print("\nLOADING EXTRA TREES TEST PREDICTIONS")

    if not PREDICTIONS_FILE.exists():
        raise FileNotFoundError(PREDICTIONS_FILE)

    df = pd.read_csv(PREDICTIONS_FILE)

    required_columns = [
        "row_index",
        "actual_price_USD",
        "extra_trees_prediction"
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing prediction columns: {missing}"
        )

    df = df.copy()

    for column in [
        "actual_price_USD",
        "extra_trees_prediction"
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.dropna(
        subset=[
            "actual_price_USD",
            "extra_trees_prediction"
        ]
    )

    if len(df) == 0:
        raise ValueError("No valid prediction records found.")

    df["residual"] = (
        df["actual_price_USD"]
        - df["extra_trees_prediction"]
    )

    df["absolute_error"] = df["residual"].abs()

    df["percentage_error"] = (
        df["absolute_error"]
        / df["actual_price_USD"]
    ) * 100

    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        ERROR_ANALYSIS_FILE,
        index=False
    )

    actual = df["actual_price_USD"]
    predicted = df["extra_trees_prediction"]
    residuals = df["residual"]
    absolute_errors = df["absolute_error"]

    print("\nDIAGNOSTIC SUMMARY")
    print("=" * 60)
    print("Test records:", len(df))
    print("Mean residual (USD):", round(residuals.mean(), 2))
    print("Residual standard deviation (USD):",
          round(residuals.std(), 2))
    print("Median absolute error (USD):",
          round(absolute_errors.median(), 2))
    print("Maximum absolute error (USD):",
          round(absolute_errors.max(), 2))
    print("=" * 60)

    # 1. Actual versus predicted prices

    fig, ax = plt.subplots(figsize=(9, 7))

    ax.scatter(
        actual,
        predicted,
        alpha=0.6
    )

    minimum = min(actual.min(), predicted.min())
    maximum = max(actual.max(), predicted.max())

    ax.plot(
        [minimum, maximum],
        [minimum, maximum],
        linestyle="--"
    )

    ax.set_title("Extra Trees: Actual vs Predicted Prices")
    ax.set_xlabel("Actual Asking Price (USD)")
    ax.set_ylabel("Predicted Asking Price (USD)")
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(
        OUTPUT_ACTUAL_PREDICTED,
        dpi=300,
        bbox_inches="tight"
    )
    plt.close(fig)

    # 2. Residuals versus predicted prices

    fig, ax = plt.subplots(figsize=(9, 7))

    ax.scatter(
        predicted,
        residuals,
        alpha=0.6
    )

    ax.axhline(
        y=0,
        linestyle="--"
    )

    ax.set_title("Extra Trees: Residuals vs Predicted Prices")
    ax.set_xlabel("Predicted Asking Price (USD)")
    ax.set_ylabel("Residual (USD)")
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(
        OUTPUT_RESIDUALS,
        dpi=300,
        bbox_inches="tight"
    )
    plt.close(fig)

    # 3. Residual distribution

    fig, ax = plt.subplots(figsize=(9, 7))

    ax.hist(
        residuals,
        bins=35,
        edgecolor="black",
        alpha=0.8
    )

    ax.axvline(
        x=0,
        linestyle="--"
    )

    ax.set_title("Extra Trees: Residual Distribution")
    ax.set_xlabel("Residual (USD)")
    ax.set_ylabel("Frequency")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(
        OUTPUT_RESIDUAL_DISTRIBUTION,
        dpi=300,
        bbox_inches="tight"
    )
    plt.close(fig)

    # 4. Absolute prediction error distribution

    fig, ax = plt.subplots(figsize=(9, 7))

    ax.hist(
        absolute_errors,
        bins=35,
        edgecolor="black",
        alpha=0.8
    )

    ax.set_title("Extra Trees: Absolute Error Distribution")
    ax.set_xlabel("Absolute Prediction Error (USD)")
    ax.set_ylabel("Frequency")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(
        OUTPUT_ABSOLUTE_ERRORS,
        dpi=300,
        bbox_inches="tight"
    )
    plt.close(fig)

    print("\nSAVED DIAGNOSTIC FILES")

    print("Error analysis:", ERROR_ANALYSIS_FILE)
    print("Actual vs predicted:", OUTPUT_ACTUAL_PREDICTED)
    print("Residuals vs predicted:", OUTPUT_RESIDUALS)
    print("Residual distribution:", OUTPUT_RESIDUAL_DISTRIBUTION)
    print("Absolute error distribution:", OUTPUT_ABSOLUTE_ERRORS)

    print("\nRESIDUAL DIAGNOSTICS COMPLETED")


if __name__ == "__main__":
    main()
