from datetime import datetime
from pathlib import Path
import json
import re
import sqlite3

import pandas as pd


SOURCE_NAME = "Inside Airbnb Munich"


def get_current_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def get_current_date() -> str:
    return datetime.now().astimezone().date().isoformat()


def normalize_date_value(value: object) -> str | None:
    if value is None:
        return None
    value_as_text = str(value)
    date_match = re.search(r"\d{4}-\d{2}-\d{2}", value_as_text)
    if date_match:
        return date_match.group(0)
    return None


def load_snapshot_date_from_manifest(manifest_path: Path) -> str:
    if not manifest_path.exists():
        return get_current_date()
    with open(manifest_path, "r", encoding="utf-8") as file:
        manifest = json.load(file)
    possible_keys = [
        "snapshot_date",
        "latest_dataset_snapshot",
        "dataset_snapshot",
        "dataset_date",
        "data_date",
        "downloaded_snapshot_date",
        "last_updated",
    ]
    def search_for_snapshot_date(data: object) -> str | None:
        if isinstance(data, dict):
            for key in possible_keys:
                if key in data:
                    normalized_date = normalize_date_value(data[key])
                    if normalized_date:
                        return normalized_date

            for value in data.values():
                result = search_for_snapshot_date(value)
                if result:
                    return result

        if isinstance(data, list):
            for item in data:
                result = search_for_snapshot_date(item)
                if result:
                    return result
        return None
    snapshot_date = search_for_snapshot_date(manifest)
    if snapshot_date:
        return snapshot_date
    return get_current_date()


def add_snapshot_metadata(
    df: pd.DataFrame,
    snapshot_date: str,
    source_name: str = SOURCE_NAME,
) -> pd.DataFrame:
    df_with_metadata = df.copy()

    df_with_metadata["snapshot_date"] = snapshot_date
    df_with_metadata["ingested_at"] = get_current_timestamp()
    df_with_metadata["source_name"] = source_name

    return df_with_metadata


def table_exists(
    connection: sqlite3.Connection,
    table_name: str,
) -> bool:
    result = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return result is not None


def save_dataframe_to_sqlite(
    df: pd.DataFrame,
    database_path: Path,
    table_name: str,
    if_exists: str = "replace",
) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        df.to_sql(
            name=table_name,
            con=connection,
            if_exists=if_exists,
            index=False,
        )


def save_cleaned_listings_snapshot(
    cleaned_listings: pd.DataFrame,
    database_path: Path,
    snapshot_date: str,
    source_file_name: str,
) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_listings_with_metadata = add_snapshot_metadata(
        df=cleaned_listings,
        snapshot_date=snapshot_date,
    )
    with sqlite3.connect(database_path) as connection:
        cleaned_listings_with_metadata.to_sql(
            name="cleaned_listings_latest",
            con=connection,
            if_exists="replace",
            index=False,
        )
        if table_exists(connection, "cleaned_listings_history"):
            connection.execute(
                """
                DELETE FROM cleaned_listings_history
                WHERE snapshot_date = ?
                """,
                (snapshot_date,),
            )
        cleaned_listings_with_metadata.to_sql(
            name="cleaned_listings_history",
            con=connection,
            if_exists="append",
            index=False,
        )
        pipeline_run = pd.DataFrame(
            [
                {
                    "snapshot_date": snapshot_date,
                    "ingested_at": get_current_timestamp(),
                    "source_name": SOURCE_NAME,
                    "source_file_name": source_file_name,
                    "row_count": len(cleaned_listings_with_metadata),
                    "database_path": str(database_path),
                }
            ]
        )
        pipeline_run.to_sql(
            name="pipeline_runs",
            con=connection,
            if_exists="append",
            index=False,
        )
    print("Saved cleaned listings to SQLite.")
    print(f"Latest table: cleaned_listings_latest")
    print(f"History table: cleaned_listings_history")
    print(f"Snapshot date: {snapshot_date}")
    print(f"Rows stored: {len(cleaned_listings_with_metadata)}")


def save_analysis_outputs_to_sqlite(
    results_dir: Path,
    database_path: Path,
) -> None:
    csv_to_table_mapping = {
        "room_type_summary.csv": "room_type_summary",
        "neighbourhood_summary.csv": "neighbourhood_summary",
        "price_by_distance_band.csv": "price_by_distance_band",
        "budget_neighbourhood_recommendations.csv": "budget_neighbourhood_recommendations",
        "tableau_kpis.csv": "tableau_kpis",
    }
    for csv_file_name, table_name in csv_to_table_mapping.items():
        csv_path = results_dir / csv_file_name
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            save_dataframe_to_sqlite(
                df=df,
                database_path=database_path,
                table_name=table_name,
                if_exists="replace",
            )
            print(f"Saved {csv_file_name} to SQLite table: {table_name}")
        else:
            print(f"Skipped missing file: {csv_file_name}")


def save_csv_outputs_to_sqlite(
    results_dir: Path,
    database_path: Path,
) -> None:
    manifest_path = results_dir / "download_manifest.json"
    snapshot_date = load_snapshot_date_from_manifest(manifest_path)

    budget_location_file = results_dir / "tableau_budget_location_listings.csv"
    basic_listing_file = results_dir / "tableau_listings.csv"

    if budget_location_file.exists():
        cleaned_listing_path = budget_location_file
    elif basic_listing_file.exists():
        cleaned_listing_path = basic_listing_file
    else:
        raise FileNotFoundError(
            "No cleaned listing CSV found. Expected either "
            "tableau_budget_location_listings.csv or tableau_listings.csv."
        )

    cleaned_listings = pd.read_csv(cleaned_listing_path)

    save_cleaned_listings_snapshot(
        cleaned_listings=cleaned_listings,
        database_path=database_path,
        snapshot_date=snapshot_date,
        source_file_name=cleaned_listing_path.name,
    )
    save_analysis_outputs_to_sqlite(
        results_dir=results_dir,
        database_path=database_path,
    )