from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_DIR / "data" / "raw"
RESULTS_DIR = PROJECT_DIR / "results"
IMAGES_DIR = PROJECT_DIR / "images"

LISTINGS_CSV = DATA_DIR / "listings.csv"
LISTINGS_CSV_GZ = DATA_DIR / "listings.csv.gz"
