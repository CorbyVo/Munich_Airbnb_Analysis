import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"
sys.path.append(str(SRC_DIR))

from munich_airbnb.analyze import (
    create_neighbourhood_summary,
    create_room_type_summary,
    save_summary_tables,
)
from munich_airbnb.clean_data import clean_listings
from munich_airbnb.load_data import load_listings
from munich_airbnb.report import print_key_findings
from munich_airbnb.visualize import create_charts


def main():
    raw_listings = load_listings()
    clean_df = clean_listings(raw_listings)

    room_type_summary = create_room_type_summary(clean_df)
    neighbourhood_summary = create_neighbourhood_summary(clean_df)

    save_summary_tables(room_type_summary, neighbourhood_summary)
    create_charts(clean_df, neighbourhood_summary)
    print_key_findings(clean_df, room_type_summary, neighbourhood_summary)


if __name__ == "__main__":
    main()
