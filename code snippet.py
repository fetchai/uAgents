import requests
from prettytable import PrettyTable

url = "https://movie-database-imdb.p.rapidapi.com/movie/"

querystring = {"name": "troy"}

headers = {
    "X-RapidAPI-Key": "e3a26d3d91msh1df956f0cff2a43p1c4efbjsn35d8a93e0c81",
    "X-RapidAPI-Host": "movie-database-imdb.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)
data = response.json()

table = PrettyTable()
table.field_names = ["Attribute", "Value"]

for key, value in data.items():
    if isinstance(value, list):
        value = ", ".join([str(item) for item in value])
    table.add_row([key, value])

print(table)
