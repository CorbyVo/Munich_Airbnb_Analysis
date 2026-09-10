from pathlib import Path
from datetime import datetime
import json
import re
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RESULTS_DIR = PROJECT_ROOT / "results"
README_TEMPLATE_PATH = PROJECT_ROOT / "README_template.md"
README_OUTPUT_PATH = PROJECT_ROOT / "README.md"

TABLEAU_DASHBOARD_URL = ("https://public.tableau.com/app/profile/van.thoi.vo/viz/MunichAirbnbMarketAnalysisDashboard/MarketOverview")

MIN_LISTINGS_PER_NEIGHBOURHOOD = 20


def normalize_column_name(column_name):
    normalized = str(column_name).strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = normalized.strip("_")
    return normalized


def find_column(dataframe, possible_names):
    normalized_columns = {
        normalize_column_name(column): column
        for column in dataframe.columns
    }
    for possible_name in possible_names:
        normalized_name = normalize_column_name(possible_name)
        if normalized_name in normalized_columns:
            return normalized_columns[normalized_name]
    return None


def read_csv_if_exists(file_path):
    if file_path.exists():
        return pd.read_csv(file_path)
    return pd.DataFrame()


def format_integer(value):
    if pd.isna(value):
        return "not available"
    return f"{int(round(float(value))):,}"


def format_price(value):
    if pd.isna(value):
        return "not available"
    return f"{int(round(float(value))):,}"


def format_distance(value):
    if pd.isna(value):
        return "not available"
    return f"{float(value):.1f}"


def format_score(value):
    if pd.isna(value):
        return "not available"
    return f"{float(value):.1f}"


def dataframe_to_markdown(dataframe):
    if dataframe.empty:
        return "_Not available yet. Run the pipeline to generate this table._"
    headers = list(dataframe.columns)
    markdown_lines = []
    markdown_lines.append("| " + " | ".join(headers) + " |")
    markdown_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in dataframe.iterrows():
        values = [str(row[column]) for column in headers]
        markdown_lines.append("| " + " | ".join(values) + " |")
    return "\n".join(markdown_lines)


def get_snapshot_date():
    manifest_path = RESULTS_DIR / "download_manifest.json"
    if not manifest_path.exists():
        return "not available"
    with open(manifest_path, "r", encoding="utf-8") as file:
        manifest = json.load(file)
    for file_record in manifest.get("files", []):
        if file_record.get("target_name") == "summary_listings":
            return file_record.get("snapshot_date", "not available")
    files = manifest.get("files", [])
    if files:
        return files[0].get("snapshot_date", "not available")
    return "not available"


def calculate_main_listing_metrics():
    listings = read_csv_if_exists(RESULTS_DIR / "tableau_listings.csv")
    default_metrics = {
        "total_listings": "not available",
        "median_price_eur_per_night": "not available",
        "most_common_room_type": "not available",
        "highest_price_room_type": "not available",
        "highest_price_neighbourhood": "not available",
    }
    if listings.empty:
        return default_metrics
    price_column = find_column(
        listings,
        ["price_eur_per_night", "price", "Price"],
    )
    room_type_column = find_column(
        listings,
        ["room_type", "Room Type"],
    )
    neighbourhood_column = find_column(
        listings,
        ["neighbourhood", "Neighbourhood"],
    )
    if price_column is None:
        return default_metrics
    listings[price_column] = pd.to_numeric(listings[price_column], errors="coerce")
    listings = listings.dropna(subset=[price_column]).copy()
    if listings.empty:
        return default_metrics
    total_listings = len(listings)
    median_price = listings[price_column].median()
    if room_type_column is not None and not listings[room_type_column].dropna().empty:
        most_common_room_type = listings[room_type_column].mode().iloc[0]
        room_type_summary = (
            listings.groupby(room_type_column)
            .agg(median_price=(price_column, "median"))
            .reset_index()
        )
        highest_room_type_row = room_type_summary.loc[
            room_type_summary["median_price"].idxmax()
        ]
        highest_price_room_type = highest_room_type_row[room_type_column]
    else:
        most_common_room_type = "not available"
        highest_price_room_type = "not available"
    if neighbourhood_column is not None:
        neighbourhood_summary = (
            listings.groupby(neighbourhood_column)
            .agg(
                listings_count=(price_column, "count"),
                median_price=(price_column, "median"),
            )
            .reset_index()
        )
        neighbourhood_summary = neighbourhood_summary[
            neighbourhood_summary["listings_count"] >= MIN_LISTINGS_PER_NEIGHBOURHOOD
        ].copy()
        if not neighbourhood_summary.empty:
            highest_neighbourhood_row = neighbourhood_summary.loc[neighbourhood_summary["median_price"].idxmax()]
            highest_price_neighbourhood = highest_neighbourhood_row[neighbourhood_column]
        else:
            highest_price_neighbourhood = "not available"
    else:
        highest_price_neighbourhood = "not available"
    return {
        "total_listings": format_integer(total_listings),
        "median_price_eur_per_night": format_price(median_price),
        "most_common_room_type": most_common_room_type,
        "highest_price_room_type": highest_price_room_type,
        "highest_price_neighbourhood": highest_price_neighbourhood,
    }


def calculate_budget_location_metrics():
    budget_summary = read_csv_if_exists(
        RESULTS_DIR / "budget_neighbourhood_recommendations.csv"
    )
    default_metrics = {
        "best_budget_neighbourhood": "not available",
        "best_budget_price_eur_per_night": "not available",
        "best_budget_distance_km": "not available",
        "cheapest_neighbourhood": "not available",
        "cheapest_price_eur_per_night": "not available",
        "cheapest_distance_km": "not available",
    }
    if budget_summary.empty:
        return default_metrics
    required_columns = [
        "neighbourhood",
        "median_price_eur_per_night",
        "median_distance_km",
        "budget_distance_score",
    ]
    missing_columns = [
        column for column in required_columns
        if column not in budget_summary.columns
    ]
    if missing_columns:
        return default_metrics
    budget_summary["median_price_eur_per_night"] = pd.to_numeric(
        budget_summary["median_price_eur_per_night"],
        errors="coerce",
    )
    budget_summary["median_distance_km"] = pd.to_numeric(
        budget_summary["median_distance_km"],
        errors="coerce",
    )
    budget_summary["budget_distance_score"] = pd.to_numeric(
        budget_summary["budget_distance_score"],
        errors="coerce",
    )
    budget_summary = budget_summary.dropna(
        subset=[
            "median_price_eur_per_night",
            "median_distance_km",
            "budget_distance_score",
        ]
    ).copy()
    if budget_summary.empty:
        return default_metrics
    best_budget_row = budget_summary.sort_values(
        "budget_distance_score"
    ).iloc[0]
    cheapest_row = budget_summary.sort_values(
        "median_price_eur_per_night"
    ).iloc[0]
    return {
        "best_budget_neighbourhood": best_budget_row["neighbourhood"],
        "best_budget_price_eur_per_night": format_price(
            best_budget_row["median_price_eur_per_night"]
        ),
        "best_budget_distance_km": format_distance(
            best_budget_row["median_distance_km"]
        ),
        "cheapest_neighbourhood": cheapest_row["neighbourhood"],
        "cheapest_price_eur_per_night": format_price(
            cheapest_row["median_price_eur_per_night"]
        ),
        "cheapest_distance_km": format_distance(
            cheapest_row["median_distance_km"]
        ),
    }


def create_distance_band_table():
    distance_summary = read_csv_if_exists(
        RESULTS_DIR / "price_by_distance_band.csv"
    )
    if distance_summary.empty:
        return "_Not available yet. Run the pipeline to generate this table._"
    required_columns = [
        "distance_band",
        "listings_count",
        "median_price_eur_per_night",
        "median_distance_km",
    ]
    missing_columns = [
        column for column in required_columns
        if column not in distance_summary.columns
    ]
    if missing_columns:
        return "_Distance summary exists, but required columns are missing._"
    table = distance_summary[required_columns].copy()
    table["listings_count"] = table["listings_count"].apply(format_integer)
    table["median_price_eur_per_night"] = table[
        "median_price_eur_per_night"
    ].apply(format_price)
    table["median_distance_km"] = table["median_distance_km"].apply(
        format_distance
    )
    table = table.rename(
        columns={
            "distance_band": "Distance band",
            "listings_count": "Listings",
            "median_price_eur_per_night": "Median nightly price (€)",
            "median_distance_km": "Median distance (km)",
        }
    )
    return dataframe_to_markdown(table)


def create_budget_recommendations_table():
    budget_summary = read_csv_if_exists(
        RESULTS_DIR / "budget_neighbourhood_recommendations.csv"
    )
    if budget_summary.empty:
        return "_Not available yet. Run the pipeline to generate this table._"
    required_columns = [
        "neighbourhood",
        "listings_count",
        "median_price_eur_per_night",
        "median_distance_km",
        "budget_distance_score",
    ]
    missing_columns = [column for column in required_columns if column not in budget_summary.columns]
    if missing_columns:
        return "_Budget recommendation summary exists, but required columns are missing._"
    table = budget_summary.sort_values("budget_distance_score").head(10).copy()
    table = table[required_columns]
    table["listings_count"] = table["listings_count"].apply(format_integer)
    table["median_price_eur_per_night"] = table[
        "median_price_eur_per_night"
    ].apply(format_price)
    table["median_distance_km"] = table["median_distance_km"].apply(format_distance)
    table["budget_distance_score"] = table["budget_distance_score"].apply(format_score)
    table = table.rename(
        columns={
            "neighbourhood": "Neighbourhood",
            "listings_count": "Listings",
            "median_price_eur_per_night": "Median nightly price (€)",
            "median_distance_km": "Median distance (km)",
            "budget_distance_score": "Budget-distance score",
        }
    )
    return dataframe_to_markdown(table)


def load_template():
    if not README_TEMPLATE_PATH.exists():
        raise FileNotFoundError(
            "README_template.md not found. Please create it in the project root."
        )
    return README_TEMPLATE_PATH.read_text(encoding="utf-8")


def replace_placeholders(template, values):
    readme_content = template
    for key, value in values.items():
        placeholder = "{{ " + key + " }}"
        readme_content = readme_content.replace(placeholder, str(value))
    unresolved_placeholders = re.findall(r"{{\s*[^}]+\s*}}", readme_content)
    if unresolved_placeholders:
        unresolved_text = ", ".join(sorted(set(unresolved_placeholders)))
        raise ValueError(f"Unresolved README placeholders: {unresolved_text}")
    return readme_content


def generate_readme():
    template = load_template()
    main_metrics = calculate_main_listing_metrics()
    budget_metrics = calculate_budget_location_metrics()
    values = {
        "snapshot_date": get_snapshot_date(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "tableau_dashboard_url": TABLEAU_DASHBOARD_URL,
        "distance_band_table": create_distance_band_table(),
        "budget_recommendations_table": create_budget_recommendations_table(),
    }
    values.update(main_metrics)
    values.update(budget_metrics)
    readme_content = replace_placeholders(template, values)
    README_OUTPUT_PATH.write_text(readme_content, encoding="utf-8")
    print("\nREADME generated successfully:")
    print(f"- {README_OUTPUT_PATH}")
    return README_OUTPUT_PATH


if __name__ == "__main__":
    generate_readme()