import pandas as pd

from munich_airbnb.config import LISTINGS_CSV, LISTINGS_CSV_GZ


def find_listings_file():
    possible_files = [LISTINGS_CSV, LISTINGS_CSV_GZ]

    for file_path in possible_files:
        if file_path.exists():
            return file_path

    raise FileNotFoundError(
        "No listings file found. Put listings.csv or listings.csv.gz inside data/raw."
    )


def load_listings():
    listings_file = find_listings_file()
    return pd.read_csv(listings_file)
