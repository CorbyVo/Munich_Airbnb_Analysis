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
