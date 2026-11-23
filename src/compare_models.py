
import json
import math
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "report" / "figures"

BASELINE_FILE = PROCESSED_DIR / "baseline_model_results.json"
RF_FILE = PROCESSED_DIR / "random_forest_model_results.json"
EXTRA_FILE = PROCESSED_DIR / "extra_trees_model_results.json"
MULTIMODAL_FILE = PROCESSED_DIR / "multimodal_model_results.json"

OUTPUT_CSV = PROCESSED_DIR / "model_comparison.csv"
OUTPUT_CHART = FIGURES_DIR / "model_comparison.png"


def load_results(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required results file was not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_metrics(results, key=None):

    metrics = results[key] if key is not None else results

    required = ["MAE_USD", "RMSE_USD", "R2"]

    missing = [
        field for field in required
        if field not in metrics
    ]

    if missing:
        raise KeyError(
            f"Missing metrics: {missing}"
        )

    extracted = {
        field: float(metrics[field])
        for field in required
    }

    if not all(
        math.isfinite(value)
        for value in extracted.values()
    ):
        raise ValueError(
            f"Invalid metrics found: {extracted}"
        )

    return extracted


def main():

    baseline = load_results(BASELINE_FILE)
    random_forest = load_results(RF_FILE)
    extra_trees = load_results(EXTRA_FILE)
    multimodal = load_results(MULTIMODAL_FILE)

    records = [
        {
            "model": "Linear Regression (Raw)",
            **extract_metrics(baseline, "linear_raw")
        },
        {
            "model": "Linear Regression (Log)",
            **extract_metrics(baseline, "linear_log")
        },
        {
            "model": "Random Forest",
            **extract_metrics(random_forest, "random_forest")
        },
        {
            "model": "Extra Trees",
            **extract_metrics(extra_trees, "extra_trees")
        },
        {
            "model": "Multimodal Neural Network",
            **extract_metrics(multimodal, "multimodal")
        }
    ]

    results = pd.DataFrame(records)

    results = results.sort_values(
        "MAE_USD",
        ascending=True
    ).reset_index(drop=True)

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results.to_csv(
        OUTPUT_CSV,
        index=False
    )

    print("\nHOUSE PRICE MODEL COMPARISON")
    print("=" * 85)

    print(
        results.to_string(
            index=False,
            float_format=lambda value: f"{value:,.4f}"
        )
    )

    print("=" * 85)

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(20, 7)
    )

    metrics = [
        ("MAE_USD", "Mean Absolute Error (USD)"),
        ("RMSE_USD", "Root Mean Squared Error (USD)"),
        ("R2", "R-squared")
    ]

    for ax, (column, title) in zip(axes, metrics):

        ordered = results.sort_values(
            column,
            ascending=(column != "R2")
        )

        ax.barh(
            ordered["model"],
            ordered[column]
        )

        ax.set_title(title)
        ax.set_xlabel(column)
        ax.invert_yaxis()
        ax.grid(
            axis="x",
            alpha=0.3
        )

    fig.suptitle(
        "Zimbabwe House Price Prediction - Model Comparison",
        fontsize=14
    )

    fig.tight_layout()

    fig.savefig(
        OUTPUT_CHART,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)

    print("\nSaved comparison CSV:", OUTPUT_CSV)
    print("Saved comparison chart:", OUTPUT_CHART)
    print("\nMODEL COMPARISON COMPLETED")


if __name__ == "__main__":
    main()
