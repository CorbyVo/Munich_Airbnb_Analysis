import pandas as pd

from munich_airbnb.config import RESULTS_DIR


def create_room_type_summary(df):
    return (
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


def create_neighbourhood_summary(df):
    return (
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


def save_summary_tables(room_type_summary, neighbourhood_summary):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    room_type_summary.to_csv(RESULTS_DIR / "room_type_summary.csv")
    neighbourhood_summary.to_csv(RESULTS_DIR / "neighbourhood_summary.csv")


def save_tableau_files(df, room_type_summary, neighbourhood_summary):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    tableau_columns = [
        "id",
        "neighbourhood",
        "room_type",
        "price",
        "minimum_nights",
        "number_of_reviews",
        "reviews_per_month",
        "availability_365",
        "availability_level",
        "has_reviews",
    ]

    df[tableau_columns].to_csv(RESULTS_DIR / "tableau_listings.csv", index=False)

    kpis = {
        "total_cleaned_listings": len(df),
        "median_price": df["price"].median(),
        "most_common_room_type": df["room_type"].value_counts().idxmax(),
        "highest_median_price_room_type": room_type_summary["median_price"].idxmax(),
        "highest_median_price_neighbourhood": neighbourhood_summary[
            "median_price"
        ].idxmax(),
    }

    pd.DataFrame([kpis]).to_csv(RESULTS_DIR / "tableau_kpis.csv", index=False)
