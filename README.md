# Munich Airbnb Market Analysis

Exploratory Data Analysis of Airbnb listings in Munich, Germany. The goal is to understand pricing patterns, room-type differences, neighbourhood trends, and listing availability.

This project is designed as a Data Analyst portfolio project for working student, internship, and junior data roles.

## Business Questions

- Which room types are most common in Munich Airbnb listings?
- How does price differ between entire apartments, private rooms, hotel rooms, and shared rooms?
- Which Munich neighbourhoods have the highest median nightly prices?
- Is there a visible relationship between price and yearly availability?
- Which neighbourhoods may offer relatively good value for visitors?

## Dataset

Source: Inside Airbnb, Munich, Bavaria, Germany.

Data date: 27 September 2025.

Recommended file:

- `listings.csv` - summary listing data, good for visualisations

Alternative file:

- `listings.csv.gz` - detailed listing data

Inside Airbnb download page:

```text
https://insideairbnb.com/get-the-data/
```

Expected local path:

```text
data/raw/listings.csv
```

or:

```text
data/raw/listings.csv.gz
```

## Skills Demonstrated

- Data loading with pandas
- Data cleaning
- Missing value handling
- Outlier filtering
- Feature engineering
- Grouping and aggregation
- Exploratory Data Analysis
- Data visualisation with seaborn and matplotlib
- Business insight communication

## Project Structure

```text
Munich_Airbnb_Analysis/
│
├── data/
│   └── raw/
│       └── listings.csv
│
├── images/
│   └── generated charts
│
├── results/
│   └── summary tables
│
├── scripts/
│   └── analyze_airbnb.py
│
├── README.md
├── requirements.txt
└── .gitignore
```

## How To Run

Install the required libraries:

```bash
pip install -r requirements.txt
```

Run the analysis:

```bash
python scripts/analyze_airbnb.py
```

The script creates:

- `results/room_type_summary.csv`
- `results/neighbourhood_summary.csv`
- `images/price_by_room_type.png`
- `images/top_neighbourhoods_by_price.png`
- `images/price_vs_availability.png`

## Method

1. Load the Munich Airbnb listings dataset.
2. Keep the columns needed for pricing and availability analysis.
3. Clean the price column.
4. Fill missing review frequency values with zero.
5. Remove listings with missing key fields.
6. Filter unrealistic nightly prices above EUR 1,000.
7. Create an availability level feature.
8. Compare price patterns by room type and neighbourhood.
9. Save result tables and charts.

## Limitations

- Prices are listing prices, not final transaction prices.
- Availability does not directly equal occupancy.
- Reviews are only an indirect signal of demand.
- The dataset represents a market snapshot for one collection date.

## Next Steps

- Add calendar data to study seasonality and Oktoberfest pricing.
- Add review data to analyze demand trends over time.
- Build a simple price prediction model after the EDA.
- Create a Streamlit dashboard for interactive exploration.
