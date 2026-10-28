
"""Safely refresh Tableau's Google Sheets source from generated CSV outputs."""

import argparse
import json
import math
import os
from pathlib import Path
from uuid import uuid4

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_TO_WORKSHEET = {
    "results/tableau_listings.csv": "tableau_listings",
    "results/tableau_kpis.csv": "tableau_kpis",
    "results/neighbourhood_summary.csv": "neighbourhood_summary",
    "results/room_type_summary.csv": "room_type_summary",
    "results/tableau_budget_location_listings.csv": "tableau_budget_location_listings",
    "results/price_by_distance_band.csv": "price_by_distance_band",
    "results/budget_neighbourhood_recommendations.csv": "budget_neighbourhood_recommendations",
}

GOOGLE_SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

MIN_ROWS = {
    "tableau_listings": 100,
    "tableau_budget_location_listings": 100,
}

UPLOAD_BATCH_SIZE = 400


def get_google_sheets_client() -> gspread.Client:
    credentials_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

    if not credentials_json:
        raise ValueError(
            "Missing GOOGLE_SERVICE_ACCOUNT_JSON environment variable."
        )

    credentials = Credentials.from_service_account_info(
        json.loads(credentials_json),
        scopes=GOOGLE_SHEETS_SCOPES,
    )

    return gspread.authorize(credentials)


def clean_value(value):
    if pd.isna(value):
        return ""

    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("CSV contains an infinite numeric value.")

    return value


def dataframe_to_sheet_values(df: pd.DataFrame) -> list[list]:
    cleaned_df = df.astype(object).where(pd.notna(df), "")

    rows = [cleaned_df.columns.tolist()]

    for row in cleaned_df.itertuples(index=False, name=None):
        rows.append([clean_value(value) for value in row])

    return rows


def load_and_validate_csvs() -> dict[str, list[list]]:
    """Read and validate ALL CSVs before connecting to Google Sheets."""
    prepared = {}

    for csv_relative_path, worksheet_name in CSV_TO_WORKSHEET.items():
        csv_path = PROJECT_ROOT / csv_relative_path

        if not csv_path.is_file():
            raise FileNotFoundError(
                f"Required CSV not found: {csv_path}"
            )

        df = pd.read_csv(csv_path)
        minimum = MIN_ROWS.get(worksheet_name, 1)

        if len(df) < minimum:
            raise ValueError(
                f"{csv_relative_path}: expected at least {minimum} data rows; "
                f"found {len(df)}."
            )

        if df.columns.has_duplicates or any(
            not str(col).strip() for col in df.columns
        ):
            raise ValueError(
                f"{csv_relative_path}: invalid column headers."
            )

        if df.isna().all(axis=1).any():
            raise ValueError(
                f"{csv_relative_path}: contains a completely empty row."
            )

        prepared[worksheet_name] = dataframe_to_sheet_values(df)

        print(f"Validated {csv_relative_path}: {len(df)} rows.")

    return prepared


def replace_all_worksheets(prepared: dict[str, list[list]]) -> None:
    """Stage new data, then atomically copy it into the existing tabs."""

    spreadsheet_id = os.environ.get("GOOGLE_SHEET_ID")

    if not spreadsheet_id:
        raise ValueError("Missing GOOGLE_SHEET_ID environment variable.")

    spreadsheet = get_google_sheets_client().open_by_key(spreadsheet_id)

    # Make sure all Tableau-connected worksheets already exist.
    targets = {
        name: spreadsheet.worksheet(name)
        for name in prepared
    }

    staging = {}

    try:
        # Upload data to temporary worksheets first.
        for name, values in prepared.items():
            stage = spreadsheet.add_worksheet(
                title=f"__staging_{name}_{uuid4().hex[:8]}",
                rows=len(values),
                cols=len(values[0]),
            )

            staging[name] = stage

            for start in range(0, len(values), UPLOAD_BATCH_SIZE):
                stage.update(
                    range_name=f"A{start + 1}",
                    values=values[start : start + UPLOAD_BATCH_SIZE],
                    raw=True,
                )

            uploaded = stage.get_all_values()

            if len(uploaded) != len(values) or uploaded[0] != values[0]:
                raise RuntimeError(
                    f"Verification failed for staging tab: {name}"
                )

            print(f"Staged and verified: {name}")

        # Prepare one atomic batch for all original worksheets.
        requests = []

        for name, values in prepared.items():
            target = targets[name]
            stage = staging[name]

            required_rows = len(values)
            required_cols = len(values[0])

            # Expand the original worksheet if necessary.
            if (
                required_rows > target.row_count
                or required_cols > target.col_count
            ):
                requests.append({
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": target.id,
                            "gridProperties": {
                                "rowCount": max(
                                    target.row_count, required_rows
                                ),
                                "columnCount": max(
                                    target.col_count, required_cols
                                ),
                            },
                        },
                        "fields": (
                            "gridProperties.rowCount,"
                            "gridProperties.columnCount"
                        ),
                    }
                })

            # Clear the existing cell values as part of the same batch.
            requests.append({
                "repeatCell": {
                    "range": {"sheetId": target.id},
                    "cell": {},
                    "fields": "userEnteredValue",
                }
            })

            # Copy the staged data into the original worksheet.
            requests.append({
                "copyPaste": {
                    "source": {
                        "sheetId": stage.id,
                        "startRowIndex": 0,
                        "endRowIndex": required_rows,
                        "startColumnIndex": 0,
                        "endColumnIndex": required_cols,
                    },
                    "destination": {
                        "sheetId": target.id,
                        "startRowIndex": 0,
                        "endRowIndex": required_rows,
                        "startColumnIndex": 0,
                        "endColumnIndex": required_cols,
                    },
                    "pasteType": "PASTE_VALUES",
                    "pasteOrientation": "NORMAL",
                }
            })

        spreadsheet.batch_update({"requests": requests})

        print("All seven existing Google Sheets tabs updated successfully.")

    finally:
        # Remove temporary worksheets, even if the upload fails.
        for stage in staging.values():
            try:
                spreadsheet.del_worksheet(stage)
            except Exception as error:
                print(
                    f"Warning: could not remove temporary tab "
                    f"{stage.title}: {error}"
                )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Check the seven CSV files without changing Google Sheets.",
    )

    args = parser.parse_args()

    prepared = load_and_validate_csvs()

    if args.validate_only:
        print("Validation passed. Google Sheets was not changed.")
        return

    replace_all_worksheets(prepared)


if __name__ == "__main__":
    main()
