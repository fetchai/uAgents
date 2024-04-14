import pandas as pd

df = pd.read_csv("../server/app/data.csv")


def get_top_5_therapists(city):
    df = pd.read_csv("app/data.csv")
    # Filter therapists based on the input city
    therapists_in_city = df[df["city"].str.lower() == city.lower()]
    if therapists_in_city.empty:
        print("No therapists found in the specified city.")
        return
    # Sort therapists based on years_of_exp in descending order and get the top 5
    top_5_therapists = therapists_in_city.sort_values(
        by="years_of_exp", ascending=False
    ).head(5)
    return top_5_therapists