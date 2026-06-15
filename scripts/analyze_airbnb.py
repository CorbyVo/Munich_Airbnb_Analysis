from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data" / "raw"
RESULTS_DIR = PROJECT_DIR / "results"
IMAGES_DIR = PROJECT_DIR / "images"


def find_listings_file():
    possible_files = [
        DATA_DIR / "listings.csv",
        DATA_DIR / "listings.csv.gz",
    ]

    for file_path in possible_files:
        if file_path.exists():
            return file_path

    raise FileNotFoundError(
        "No listings file found. Put listings.csv or listings.csv.gz inside data/raw."
    )


def clean_price_column(price_series):
    return (
        price_series.astype(str)
        .str.replace(r"[$,EUReur ]", "", regex=True)
        .replace("nan", pd.NA)
        .astype(float)
    )


def load_and_clean_data():
    listings_file = find_listings_file()
    df = pd.read_csv(listings_file)

    selected_columns = [
        "id",
        "name",
        "host_id",
        "neighbourhood",
        "room_type",
        "price",
        "minimum_nights",
        "number_of_reviews",
        "reviews_per_month",
        "availability_365",
    ]

    existing_columns = [column for column in selected_columns if column in df.columns]
    df = df[existing_columns].copy()

    df["price"] = clean_price_column(df["price"])
    df["reviews_per_month"] = df["reviews_per_month"].fillna(0)

    df = df.dropna(subset=["price", "neighbourhood", "room_type"])
    df = df[(df["price"] > 0) & (df["price"] <= 1000)]

    df["availability_level"] = pd.cut(
        df["availability_365"],
        bins=[-1, 30, 180, 365],
        labels=["Low", "Medium", "High"],
    )

    df["has_reviews"] = df["number_of_reviews"] > 0

    return df


def save_summary_tables(df):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    room_type_summary = (
        df.groupby("room_type")
        .agg(
            listings=("id", "count"),
            median_price=("price", "median"),
            average_price=("price", "mean"),
            median_availability=("availability_365", "median"),
            median_reviews=("number_of_reviews", "median"),
        )
        .sort_values("median_price", ascending=False)
    )

    neighbourhood_summary = (
        df.groupby("neighbourhood")
        .agg(
            listings=("id", "count"),
            median_price=("price", "median"),
            average_price=("price", "mean"),
            median_availability=("availability_365", "median"),
            median_reviews=("number_of_reviews", "median"),
        )
        .query("listings >= 20")
        .sort_values("median_price", ascending=False)
    )

    room_type_summary.to_csv(RESULTS_DIR / "room_type_summary.csv")
    neighbourhood_summary.to_csv(RESULTS_DIR / "neighbourhood_summary.csv")

    return room_type_summary, neighbourhood_summary


def create_charts(df, neighbourhood_summary):
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(9, 5))
    sns.boxplot(data=df, x="room_type", y="price")
    plt.title("Price Distribution by Room Type")
    plt.xlabel("Room type")
    plt.ylabel("Price per night (EUR)")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "price_by_room_type.png", dpi=150)
    plt.close()

    top_neighbourhoods = neighbourhood_summary.head(10).reset_index()

    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=top_neighbourhoods,
        x="median_price",
        y="neighbourhood",
        color="#4C78A8",
    )
    plt.title("Top 10 Munich Neighbourhoods by Median Airbnb Price")
    plt.xlabel("Median price per night (EUR)")
    plt.ylabel("Neighbourhood")
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "top_neighbourhoods_by_price.png", dpi=150)
    plt.close()

    plt.figure(figsize=(9, 5))
    sns.scatterplot(
        data=df,
        x="availability_365",
        y="price",
        hue="room_type",
        alpha=0.6,
    )
    plt.title("Price vs Availability")
    plt.xlabel("Available days per year")
    plt.ylabel("Price per night (EUR)")
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "price_vs_availability.png", dpi=150)
    plt.close()


def print_key_findings(df, room_type_summary, neighbourhood_summary):
    total_listings = len(df)
    median_price = df["price"].median()
    most_common_room_type = df["room_type"].value_counts().idxmax()
    most_expensive_room_type = room_type_summary["median_price"].idxmax()
    most_expensive_neighbourhood = neighbourhood_summary["median_price"].idxmax()

    print("Munich Airbnb Analysis - Key Findings")
    print("-------------------------------------")
    print(f"Total cleaned listings: {total_listings:,}")
    print(f"Median price per night: EUR {median_price:,.0f}")
    print(f"Most common room type: {most_common_room_type}")
    print(f"Room type with highest median price: {most_expensive_room_type}")
    print(f"Neighbourhood with highest median price: {most_expensive_neighbourhood}")
    print()
    print("Result tables saved in: results/")
    print("Charts saved in: images/")


def main():
    df = load_and_clean_data()
    room_type_summary, neighbourhood_summary = save_summary_tables(df)
    create_charts(df, neighbourhood_summary)
    print_key_findings(df, room_type_summary, neighbourhood_summary)


if __name__ == "__main__":
    main()
