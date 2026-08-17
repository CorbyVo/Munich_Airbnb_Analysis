import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from munich_airbnb.database import save_csv_outputs_to_sqlite


def main() -> None:
    results_dir = PROJECT_ROOT / "results"
    database_path = PROJECT_ROOT / "data" / "processed" / "munich_airbnb.sqlite"

    save_csv_outputs_to_sqlite(
        results_dir=results_dir,
        database_path=database_path,
    )

    print(f"\nSQLite database created at: {database_path}")


if __name__ == "__main__":
    main()