import matplotlib.pyplot as plt
import seaborn as sns

from munich_airbnb.config import IMAGES_DIR


def save_price_by_room_type_chart(df):
    plt.figure(figsize=(9, 5))
    sns.boxplot(data=df, x="room_type", y="price")
    plt.title("Price Distribution by Room Type")
    plt.xlabel("Room type")
    plt.ylabel("Price per night (EUR)")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "price_by_room_type.png", dpi=150)
    plt.close()


def save_top_neighbourhoods_chart(neighbourhood_summary):
    top_neighbourhoods = neighbourhood_summary.head(10).reset_index()

    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=top_neighbourhoods,
        x="median_price",
        y="neighbourhood",
        color="#4C78A8",
    )
    plt.title("Top 10 Munich Neighbourhoods by Median Airbnb Price")
    plt.xlabel("Median price per night (EUR)")
    plt.ylabel("Neighbourhood")
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "top_neighbourhoods_by_price.png", dpi=150)
    plt.close()


def save_price_vs_availability_chart(df):
    plt.figure(figsize=(9, 5))
    sns.scatterplot(
        data=df,
        x="availability_365",
        y="price",
        hue="room_type",
        alpha=0.6,
    )
    plt.title("Price vs Availability")
    plt.xlabel("Available days per year")
    plt.ylabel("Price per night (EUR)")
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "price_vs_availability.png", dpi=150)
    plt.close()


def create_charts(df, neighbourhood_summary):
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    save_price_by_room_type_chart(df)
    save_top_neighbourhoods_chart(neighbourhood_summary)
    save_price_vs_availability_chart(df)
