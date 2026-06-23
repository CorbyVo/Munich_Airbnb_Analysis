from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))


from munich_airbnb.budget_location_analysis import run_budget_location_analysis


if __name__ == "__main__":
    run_budget_location_analysis()