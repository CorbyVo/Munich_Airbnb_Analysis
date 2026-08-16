from pathlib import Path
import argparse
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from munich_airbnb.pipeline import run_pipeline


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run the full Munich Airbnb data pipeline."
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Use existing local raw data files and skip downloading new data.",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Download fresh raw data even if local files already exist.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    run_pipeline(
        download_data=not args.skip_download,
        force_download=args.force_download,
    )