import pandas as pd


SELECTED_COLUMNS = [
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


def select_available_columns(df):
    existing_columns = [column for column in SELECTED_COLUMNS if column in df.columns]
    return df[existing_columns].copy()


def clean_price_column(price_series):
    cleaned_price = (
        price_series.astype(str)
        .str.replace(r"[$,€,\s]", "", regex=True)
        .str.replace("EUR", "", regex=False)
        .str.replace("eur", "", regex=False)
    )

    return pd.to_numeric(cleaned_price, errors="coerce")


def add_availability_level(df):
    df["availability_level"] = pd.cut(
        df["availability_365"],
        bins=[-1, 30, 180, 365],
        labels=["Low", "Medium", "High"],
    )
    return df


def clean_listings(df):
    df = select_available_columns(df)

    df["price"] = clean_price_column(df["price"])
    df["reviews_per_month"] = df["reviews_per_month"].fillna(0)

    df = df.dropna(subset=["price", "neighbourhood", "room_type"])
    df = df[(df["price"] > 0) & (df["price"] <= 1000)]

    df = add_availability_level(df)
    df["has_reviews"] = df["number_of_reviews"] > 0

    return df
