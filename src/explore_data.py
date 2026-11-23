
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "cleaned_house_listings.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "report" / "figures"
SUMMARY_DIR = PROJECT_ROOT / "data" / "processed"

sns.set_theme(style="whitegrid")


def explore_data():
    """Perform comprehensive exploratory data analysis."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    if df.empty:
        raise ValueError("The cleaned dataset is empty.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    numeric_columns = [
        "price", "bedrooms", "bathrooms",
        "garages", "land_size", "floor_size"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    print("=" * 65)
    print("ZIMBABWE HOUSE PRICE PROJECT - EXPLORATORY DATA ANALYSIS")
    print("=" * 65)

    # 1. Dataset overview
    print("\n1. DATASET OVERVIEW")
    print("Shape:", df.shape)
    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values:")
    missing = df.isnull().sum().to_frame("missing_count")
    missing["missing_percentage"] = (
        missing["missing_count"] / len(df) * 100
    ).round(2)
    print(missing)

    missing.to_csv(SUMMARY_DIR / "missing_values_summary.csv")

    # 2. Price statistics
    print("\n2. ASKING PRICE STATISTICS")
    print(df["price"].describe())

    print("\nMean:", round(df["price"].mean(), 2))
    print("Median:", round(df["price"].median(), 2))
    print("Standard deviation:", round(df["price"].std(), 2))
    print("Skewness:", round(df["price"].skew(), 3))

    # 3. Property type analysis
    print("\n3. PROPERTY TYPE DISTRIBUTION")
    print(df["property_type"].value_counts(dropna=False))

    type_summary = (
        df.groupby("property_type")["price"]
        .agg(["count", "mean", "median", "min", "max"])
        .sort_values("median", ascending=False)
    )

    print("\nPrices by property type:")
    print(type_summary)

    type_summary.to_csv(
        SUMMARY_DIR / "prices_by_property_type.csv"
    )

    # 4. City analysis
    print("\n4. PRICES BY CITY")

    city_summary = (
        df.groupby("city")["price"]
        .agg(["count", "mean", "median"])
        .sort_values("median", ascending=False)
    )

    print(city_summary)

    city_summary.to_csv(SUMMARY_DIR / "prices_by_city.csv")

    # 5. Bedroom analysis
    print("\n5. PRICES BY BEDROOMS")

    bedroom_summary = (
        df.groupby("bedrooms")["price"]
        .agg(["count", "mean", "median"])
        .sort_index()
    )

    print(bedroom_summary)

    bedroom_summary.to_csv(
        SUMMARY_DIR / "prices_by_bedrooms.csv"
    )

    # 6. Numerical correlations
    print("\n6. NUMERICAL CORRELATIONS")

    correlation = df[numeric_columns].corr(method="spearman")

    print(correlation.round(3))

    correlation.to_csv(
        SUMMARY_DIR / "feature_correlations.csv"
    )

    # 7. Price distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(df["price"].dropna(), bins=40, kde=True)
    plt.title("Distribution of Property Asking Prices")
    plt.xlabel("Asking Price (USD)")
    plt.ylabel("Number of Listings")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "price_distribution.png",
        dpi=300
    )
    plt.close()

    # 8. Log price distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(
        df.loc[df["price"] > 0, "price"].apply("log"),
        bins=40,
        kde=True
    )
    plt.title("Distribution of Log-transformed Asking Prices")
    plt.xlabel("Natural Log of Asking Price")
    plt.ylabel("Number of Listings")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "log_price_distribution.png",
        dpi=300
    )
    plt.close()

    # 9. Prices by bedrooms
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df, x="bedrooms", y="price")
    plt.title("Property Prices by Number of Bedrooms")
    plt.xlabel("Bedrooms")
    plt.ylabel("Asking Price (USD)")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "prices_by_bedrooms.png",
        dpi=300
    )
    plt.close()

    # 10. Prices by property type
    plt.figure(figsize=(12, 7))
    sns.boxplot(
        data=df,
        x="property_type",
        y="price"
    )
    plt.title("Property Prices by Property Type")
    plt.xlabel("Property Type")
    plt.ylabel("Asking Price (USD)")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "prices_by_property_type.png",
        dpi=300
    )
    plt.close()

    # 11. Median prices by city
    top_cities = (
        df.groupby("city")["price"]
        .agg(["count", "median"])
        .query("count >= 10")
        .sort_values("median", ascending=False)
        .head(15)
    )

    plt.figure(figsize=(12, 7))
    sns.barplot(
        x=top_cities["median"].values,
        y=top_cities.index
    )
    plt.title("Median Asking Prices in Top 15 Cities")
    plt.xlabel("Median Asking Price (USD)")
    plt.ylabel("City")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "prices_by_city.png",
        dpi=300
    )
    plt.close()

    # 12. Land size versus price
    land_data = df[
        (df["land_size"] > 0) &
        (df["price"] > 0)
    ]

    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=land_data,
        x="land_size",
        y="price",
        alpha=0.5
    )
    plt.title("Land Size versus Property Asking Price")
    plt.xlabel("Land Size (m²)")
    plt.ylabel("Asking Price (USD)")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "land_size_vs_price.png",
        dpi=300
    )
    plt.close()

    # 13. Floor size versus price
    floor_data = df[
        (df["floor_size"] > 0) &
        (df["price"] > 0)
    ]

    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=floor_data,
        x="floor_size",
        y="price",
        alpha=0.5
    )
    plt.title("Floor Size versus Property Asking Price")
    plt.xlabel("Floor Size (m²)")
    plt.ylabel("Asking Price (USD)")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "floor_size_vs_price.png",
        dpi=300
    )
    plt.close()

    # 14. Missing data chart
    missing_percent = (
        df.isnull().mean() * 100
    ).sort_values(ascending=False)

    missing_percent = missing_percent[
        missing_percent > 0
    ]

    plt.figure(figsize=(11, 6))
    sns.barplot(
        x=missing_percent.values,
        y=missing_percent.index
    )
    plt.title("Missing Values by Feature")
    plt.xlabel("Missing Values (%)")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "missing_values.png",
        dpi=300
    )
    plt.close()

    # 15. Correlation heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        correlation,
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        center=0
    )
    plt.title("Spearman Correlation Between Numerical Features")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "correlation_heatmap.png",
        dpi=300
    )
    plt.close()

    print("\n" + "=" * 65)
    print("EDA COMPLETED SUCCESSFULLY")
    print("=" * 65)
    print("Records analysed:", len(df))
    print("Charts saved:", OUTPUT_DIR)
    print("Summary CSV files saved:", SUMMARY_DIR)


if __name__ == "__main__":
    explore_data()
