from pathlib import Path
from datetime import datetime
import subprocess
import sys

from munich_airbnb.download_data import download_latest_munich_data
from munich_airbnb.readme_generator import generate_readme
from munich_airbnb.database import save_csv_outputs_to_sqlite


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results"
DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "munich_airbnb.sqlite"


def run_command(command, step_name):
    print("\n" + "=" * 60)
    print(f"Running step: {step_name}")
    print("=" * 60)

    result = subprocess.run( command,cwd=PROJECT_ROOT,)

    if result.returncode != 0:
        raise RuntimeError(f"Pipeline step failed: {step_name}")


def run_pipeline(download_data=True, force_download=False):
    start_time = datetime.now()

    print("Munich Airbnb automated data pipeline")
    print("=" * 60)
    print(f"Pipeline started at: {start_time.isoformat(timespec='seconds')}")

    if download_data:
        download_latest_munich_data(force=force_download)
    else:
        print("Skipping data download step.")

    run_command(
        [sys.executable, "scripts/run_analysis.py"],
        "Main listing analysis",
    )

    budget_analysis_script = PROJECT_ROOT / "scripts" / "run_budget_location_analysis.py"

    if budget_analysis_script.exists():
        run_command(
            [sys.executable, "scripts/run_budget_location_analysis.py"],
            "Budget-location analysis",
        )
    else:
        print("\nSkipping budget-location analysis because the runner file was not found.")

    print("\n" + "=" * 60)
    print("Running step: README generation")
    print("=" * 60)

    generate_readme()

    print("\n" + "=" * 60)
    print("Running step: SQLite export")
    print("=" * 60)

    save_csv_outputs_to_sqlite( results_dir=RESULTS_DIR,database_path=DATABASE_PATH,)

    print(f"SQLite database updated: {DATABASE_PATH}")

    end_time = datetime.now()
    duration = end_time - start_time

    print("\n" + "=" * 60)
    print("Pipeline finished successfully")
    print("=" * 60)
    print(f"Finished at: {end_time.isoformat(timespec='seconds')}")
    print(f"Duration: {duration}")

    print("\nUpdated folders and files:")
    print("- data/raw/")
    print("- data/processed/munich_airbnb.sqlite")
    print("- results/")
    print("- images/")
    print("- README.md")