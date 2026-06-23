from pathlib import Path
from math import radians, sin, cos, sqrt, atan2

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
RESULTS_DIR = PROJECT_ROOT / "results"
IMAGES_DIR = PROJECT_ROOT / "images"

LISTINGS_FILE = RAW_DATA_DIR / "listings.csv"
CALENDAR_FILE_GZ = RAW_DATA_DIR / "calendar.csv.gz"

OKTOBERFEST_START = pd.Timestamp("2025-09-20")
OKTOBERFEST_END = pd.Timestamp("2025-10-05")

THERESIENWIESE_LAT = 48.1319
THERESIENWIESE_LON = 11.5495

MIN_LISTINGS_PER_NEIGHBOURHOOD = 20
PRICE_UNIT = "EUR per night"


def clean_price_column(price_series):
    cleaned_price = (
        price_series.astype(str)
        .str.replace(r"[$,€,\s]", "", regex=True)
        .str.replace("EUR", "", regex=False)
        .str.replace("eur", "", regex=False)
    )

    return pd.to_numeric(cleaned_price, errors="coerce")


def calculate_distance_km(lat1, lon1, lat2, lon2):
    earth_radius_km = 6371

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    lat_diff = lat2_rad - lat1_rad
    lon_diff = lon2_rad - lon1_rad

    a = (
        sin(lat_diff / 2) ** 2
        + cos(lat1_rad) * cos(lat2_rad) * sin(lon_diff / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius_km * c


def classify_distance_band(distance_km):
    if distance_km <= 2:
        return "0-2 km from Oktoberfest"

    if distance_km <= 5:
        return "2-5 km from Oktoberfest"

    if distance_km <= 10:
        return "5-10 km from Oktoberfest"

    return "10+ km from Oktoberfest"


def load_listings_data():
    if not LISTINGS_FILE.exists():
        raise FileNotFoundError(
            "listings.csv not found. Please put listings.csv in data/raw/."
        )

    df = pd.read_csv(LISTINGS_FILE)
    df.columns = df.columns.str.lower().str.strip()

    return df


def clean_listings_data(df):
    required_columns = [
        "id",
        "neighbourhood",
        "latitude",
        "longitude",
        "room_type",
        "price",
    ]

    missing_columns = [column for column in required_columns if column not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns in listings.csv: {missing_columns}")

    useful_columns = required_columns.copy()

    optional_columns = [
        "minimum_nights",
        "number_of_reviews",
        "reviews_per_month",
        "availability_365",
    ]

    for column in optional_columns:
        if column in df.columns:
            useful_columns.append(column)

    df = df[useful_columns].copy()

    df["price_eur_per_night"] = clean_price_column(df["price"])
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    df = df.dropna(
        subset=[
            "id",
            "neighbourhood",
            "latitude",
            "longitude",
            "room_type",
            "price_eur_per_night",
        ]
    )

    df = df[
        (df["price_eur_per_night"] > 0)
        & (df["price_eur_per_night"] <= 1000)
    ].copy()

    df["price_unit"] = PRICE_UNIT

    df["distance_to_oktoberfest_km"] = df.apply(
        lambda row: calculate_distance_km(
            row["latitude"],
            row["longitude"],
            THERESIENWIESE_LAT,
            THERESIENWIESE_LON,
        ),
        axis=1,
    )

    df["distance_band"] = df["distance_to_oktoberfest_km"].apply(classify_distance_band)

    df = df.drop(columns=["price"], errors="ignore")

    return df


def load_oktoberfest_availability():
    if not CALENDAR_FILE_GZ.exists():
        return pd.DataFrame()

    calendar = pd.read_csv(
        CALENDAR_FILE_GZ,
        compression="infer",
        usecols=["listing_id", "date", "available"],
    )

    calendar.columns = calendar.columns.str.lower().str.strip()
    calendar["date"] = pd.to_datetime(calendar["date"], errors="coerce")
    calendar["available"] = calendar["available"].astype(str).str.lower().str.strip()
    calendar["is_available"] = calendar["available"].isin(["t", "true", "1", "yes"])

    oktoberfest_calendar = calendar[
        (calendar["date"] >= OKTOBERFEST_START)
        & (calendar["date"] <= OKTOBERFEST_END)
    ].copy()

    if oktoberfest_calendar.empty:
        return pd.DataFrame()

    availability_summary = (
        oktoberfest_calendar.groupby("listing_id")
        .agg(
            oktoberfest_observed_days=("date", "nunique"),
            oktoberfest_available_days=("is_available", "sum"),
        )
        .reset_index()
    )

    availability_summary["available_during_observed_oktoberfest"] = (
        availability_summary["oktoberfest_available_days"] > 0
    )

    return availability_summary


def add_oktoberfest_availability(listings, availability_summary):
    if availability_summary.empty:
        listings["oktoberfest_observed_days"] = pd.NA
        listings["oktoberfest_available_days"] = pd.NA
        listings["available_during_observed_oktoberfest"] = pd.NA
        return listings

    listings = listings.merge(
        availability_summary,
        left_on="id",
        right_on="listing_id",
        how="left",
    )

    listings["oktoberfest_available_days"] = listings[
        "oktoberfest_available_days"
    ].fillna(0)

    listings["oktoberfest_observed_days"] = listings[
        "oktoberfest_observed_days"
    ].fillna(0)

    listings["available_during_observed_oktoberfest"] = listings[
        "available_during_observed_oktoberfest"
    ].fillna(False)

    listings = listings.drop(columns=["listing_id"], errors="ignore")

    return listings


def create_distance_band_summary(listings):
    distance_order = [
        "0-2 km from Oktoberfest",
        "2-5 km from Oktoberfest",
        "5-10 km from Oktoberfest",
        "10+ km from Oktoberfest",
    ]

    summary = (
        listings.groupby("distance_band")
        .agg(
            listings_count=("id", "count"),
            median_price_eur_per_night=("price_eur_per_night", "median"),
            average_price_eur_per_night=("price_eur_per_night", "mean"),
            median_distance_km=("distance_to_oktoberfest_km", "median"),
        )
        .reset_index()
    )

    summary["price_unit"] = PRICE_UNIT

    summary["distance_band"] = pd.Categorical(
        summary["distance_band"],
        categories=distance_order,
        ordered=True,
    )

    summary = summary.sort_values("distance_band")

    return summary


def create_neighbourhood_budget_summary(listings):
    summary = (
        listings.groupby("neighbourhood")
        .agg(
            listings_count=("id", "count"),
            median_price_eur_per_night=("price_eur_per_night", "median"),
            average_price_eur_per_night=("price_eur_per_night", "mean"),
            median_distance_km=("distance_to_oktoberfest_km", "median"),
            entire_home_share=("room_type", lambda x: (x == "Entire home/apt").mean()),
            available_during_oktoberfest_count=(
                "available_during_observed_oktoberfest",
                lambda x: x.fillna(False).sum(),
            ),
        )
        .reset_index()
    )

    summary = summary[summary["listings_count"] >= MIN_LISTINGS_PER_NEIGHBOURHOOD].copy()

    summary["price_unit"] = PRICE_UNIT

    summary["oktoberfest_availability_share"] = (
        summary["available_during_oktoberfest_count"] / summary["listings_count"]
    )

    summary["budget_distance_score"] = (
        summary["median_price_eur_per_night"]
        + summary["median_distance_km"] * 10
    )

    summary = summary.sort_values("budget_distance_score")

    return summary


def create_output_dictionary():
    output_dictionary = pd.DataFrame(
        [
            {
                "file_name": "tableau_budget_location_listings.csv",
                "column_name": "price_eur_per_night",
                "definition": "Advertised daily/nightly Airbnb listing price in EUR from listings.csv.",
            },
            {
                "file_name": "price_by_distance_band.csv",
                "column_name": "median_price_eur_per_night",
                "definition": "Median advertised nightly price in EUR for listings in each distance band.",
            },
            {
                "file_name": "price_by_distance_band.csv",
                "column_name": "average_price_eur_per_night",
                "definition": "Average advertised nightly price in EUR for listings in each distance band.",
            },
            {
                "file_name": "budget_neighbourhood_recommendations.csv",
                "column_name": "median_price_eur_per_night",
                "definition": "Median advertised nightly price in EUR for listings in each neighbourhood.",
            },
            {
                "file_name": "budget_neighbourhood_recommendations.csv",
                "column_name": "median_distance_km",
                "definition": "Median distance in kilometers from the neighbourhood's listings to Theresienwiese.",
            },
            {
                "file_name": "budget_neighbourhood_recommendations.csv",
                "column_name": "budget_distance_score",
                "definition": "Simple ranking score: median nightly price in EUR plus 10 times median distance in km. Lower is better.",
            },
            {
                "file_name": "all budget-location outputs",
                "column_name": "price_unit",
                "definition": "EUR per night. Prices are not monthly rent and not full-trip costs.",
            },
        ]
    )

    return output_dictionary


def save_results(listings, distance_summary, neighbourhood_summary, output_dictionary):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    listings.to_csv(
        RESULTS_DIR / "tableau_budget_location_listings.csv",
        index=False,
    )

    distance_summary.to_csv(
        RESULTS_DIR / "price_by_distance_band.csv",
        index=False,
    )

    neighbourhood_summary.to_csv(
        RESULTS_DIR / "budget_neighbourhood_recommendations.csv",
        index=False,
    )

    output_dictionary.to_csv(
        RESULTS_DIR / "budget_location_output_dictionary.csv",
        index=False,
    )


def plot_price_by_distance_band(distance_summary):
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(
        distance_summary["distance_band"].astype(str),
        distance_summary["median_price_eur_per_night"],
    )

    ax.set_title("Median Nightly Airbnb Price by Distance to Oktoberfest")
    ax.set_xlabel("Distance to Oktoberfest")
    ax.set_ylabel("Median nightly price (€)")

    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "price_by_distance_band.png", dpi=150)
    plt.close()


def plot_budget_neighbourhoods(neighbourhood_summary):
    chart_data = neighbourhood_summary.head(10).sort_values("budget_distance_score")

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.barh(
        chart_data["neighbourhood"],
        chart_data["budget_distance_score"],
    )

    ax.set_title("Budget-Friendly Munich Neighbourhoods: Nightly Price vs Distance")
    ax.set_xlabel("Budget-distance score")
    ax.set_ylabel("Neighbourhood")

    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "budget_neighbourhood_recommendations.png", dpi=150)
    plt.close()


def print_findings(distance_summary, neighbourhood_summary):
    print("Munich Airbnb Budget vs Distance Analysis")
    print("=" * 50)
    print(f"Price interpretation: {PRICE_UNIT}")
    print("Prices are listing-level advertised nightly prices, not monthly rent.")
    print("Calendar price values were unavailable, so this is not dynamic event pricing.")

    print("\nMedian nightly price by distance band:")

    for _, row in distance_summary.iterrows():
        print(
            f"- {row['distance_band']}: "
            f"EUR {row['median_price_eur_per_night']:.0f} per night "
            f"from {row['listings_count']:,} listings"
        )

    best_budget_area = neighbourhood_summary.iloc[0]
    cheapest_area = neighbourhood_summary.sort_values(
        "median_price_eur_per_night"
    ).iloc[0]

    print("\nBest budget-distance neighbourhood:")
    print(
        f"- {best_budget_area['neighbourhood']}: "
        f"EUR {best_budget_area['median_price_eur_per_night']:.0f} per night, "
        f"{best_budget_area['median_distance_km']:.1f} km from Oktoberfest"
    )

    print("\nCheapest neighbourhood with enough listings:")
    print(
        f"- {cheapest_area['neighbourhood']}: "
        f"EUR {cheapest_area['median_price_eur_per_night']:.0f} per night, "
        f"{cheapest_area['median_distance_km']:.1f} km from Oktoberfest"
    )

    print("\nGenerated files:")
    print("- results/tableau_budget_location_listings.csv")
    print("- results/price_by_distance_band.csv")
    print("- results/budget_neighbourhood_recommendations.csv")
    print("- results/budget_location_output_dictionary.csv")
    print("- images/price_by_distance_band.png")
    print("- images/budget_neighbourhood_recommendations.png")


def run_budget_location_analysis():
    raw_listings = load_listings_data()
    clean_listings = clean_listings_data(raw_listings)

    availability_summary = load_oktoberfest_availability()
    listings_with_availability = add_oktoberfest_availability(
        clean_listings,
        availability_summary,
    )

    distance_summary = create_distance_band_summary(listings_with_availability)
    neighbourhood_summary = create_neighbourhood_budget_summary(
        listings_with_availability
    )
    output_dictionary = create_output_dictionary()

    save_results(
        listings_with_availability,
        distance_summary,
        neighbourhood_summary,
        output_dictionary,
    )

    plot_price_by_distance_band(distance_summary)
    plot_budget_neighbourhoods(neighbourhood_summary)

    print_findings(distance_summary, neighbourhood_summary)

    return listings_with_availability, distance_summary, neighbourhood_summary