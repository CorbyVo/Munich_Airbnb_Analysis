from pathlib import Path
import sqlite3

import pandas as pd


def save_dataframe_to_sqlite(
    df: pd.DataFrame,
    database_path: Path,
    table_name: str,
) -> None:
    """
    Save one pandas DataFrame into a SQLite table.
    If the table already exists, it will be replaced.
    """
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        df.to_sql(
            name=table_name,
            con=connection,
            if_exists="replace",
            index=False,
        )


def save_csv_outputs_to_sqlite(
    results_dir: Path,
    database_path: Path,
) -> None:
    """
    Read selected cleaned CSV output files from the results folder
    and save them as tables inside a SQLite database.
    """
    csv_to_table_mapping = {
        "tableau_listings.csv": "cleaned_listings",
        "room_type_summary.csv": "room_type_summary",
        "neighbourhood_summary.csv": "neighbourhood_summary",
        "price_by_distance_band.csv": "price_by_distance_band",
        "budget_neighbourhood_recommendations.csv": "budget_neighbourhood_recommendations",
        "tableau_budget_location_listings.csv": "budget_location_listings",
    }

    for csv_file_name, table_name in csv_to_table_mapping.items():
        csv_path = results_dir / csv_file_name

        if csv_path.exists():
            df = pd.read_csv(csv_path)
            save_dataframe_to_sqlite(df, database_path, table_name)
            print(f"Saved {csv_file_name} to SQLite table: {table_name}")
        else:
            print(f"Skipped missing file: {csv_file_name}")